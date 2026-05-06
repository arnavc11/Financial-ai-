import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64
import warnings
warnings.filterwarnings("ignore")

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

DARK   = "#0a1628"
CARD   = "#111827"
ACCENT = "#00d4aa"
GOLD   = "#f5c842"
RED    = "#ff4d6a"
BLUE   = "#3b82f6"
TEXT   = "#e2e8f0"
GRID   = "#1e2d45"

class StockPredictor:

    def __init__(self, sequence_length: int = 60):
        self.sequence_length = sequence_length
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        self.is_trained = False

    def _fetch_data(self, symbol: str, period: str = "2y") -> pd.DataFrame:
        import yfinance as yf
        suffix = ".NS"
        df = yf.download(f"{symbol}{suffix}", period=period,
                         auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty:
            raise ValueError(f"No data found for {symbol}")
        return df

    def _prepare_sequences(self, data: np.ndarray):
        X, y = [], []
        for i in range(self.sequence_length, len(data)):
            X.append(data[i - self.sequence_length:i, 0])
            y.append(data[i, 0])
        return np.array(X), np.array(y)

    def _build_lstm_model(self, input_shape: tuple):
        model = Sequential([
            LSTM(100, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])

        model.compile(optimizer="adam", loss="mean_squared_error")
        return model

    def _statistical_fallback(self, close_prices: pd.Series, days_ahead: int = 7):
        prices = close_prices.values
        n = len(prices)

        recent = prices[-30:]
        x = np.arange(len(recent))

        slope, intercept = np.polyfit(x, recent, 1)

        predictions = []
        for i in range(1, days_ahead + 1):
            pred = slope * (len(recent) + i) + intercept

            noise = np.std(recent[-10:]) * 0.1
            pred += np.random.normal(0, noise)
            predictions.append(max(0, pred))

        return np.array(predictions)

    def predict(self, symbol: str, days_ahead: int = 7):

        df = self._fetch_data(symbol)
        close = df["Close"].squeeze()
        dates = df.index

        current_price = float(close.iloc[-1])
        prices_array = close.values.reshape(-1, 1)

        scaled = self.scaler.fit_transform(prices_array)

        if TENSORFLOW_AVAILABLE and len(scaled) > self.sequence_length + 50:
            predictions, test_actual, test_predicted, metrics = \
                self._lstm_predict(scaled, prices_array, days_ahead)
            method = "LSTM Neural Network"
        else:

            predictions = self._statistical_fallback(close, days_ahead)
            test_actual = close.values[-30:]
            test_predicted = self._statistical_fallback(
                close.iloc[:-30], len(test_actual))
            metrics = self._calc_metrics(test_actual, test_predicted, current_price)
            method = "Statistical (install TensorFlow for LSTM)"

        chart_b64 = self._generate_chart(
            symbol, close, dates, predictions, days_ahead)

        last_pred = float(predictions[-1])
        direction = "UP 📈" if last_pred > current_price else "DOWN 📉"
        change_pct = ((last_pred - current_price) / current_price) * 100

        interpretation = self._interpret(
            symbol, current_price, predictions, metrics, change_pct)

        return {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "current_price_formatted": f"Rs.{current_price:,.2f}",
            "method": method,
            "predictions": {
                f"day_{i+1}": {
                    "price": round(float(p), 2),
                    "formatted": f"Rs.{float(p):,.2f}",
                    "change_pct": round(((float(p) - current_price) / current_price) * 100, 2)
                }
                for i, p in enumerate(predictions)
            },
            "7_day_direction": direction,
            "7_day_change_pct": round(change_pct, 2),
            "metrics": metrics,
            "interpretation": interpretation,
            "chart_base64": chart_b64,
            "disclaimer": (
                "⚠️ ML predictions are probabilistic, not guaranteed. "
                "Stock markets are influenced by news, global events, and human sentiment "
                "which no model can fully capture. Use this as ONE input, not the only one. "
                "Not SEBI-registered investment advice."
            )
        }

    def _lstm_predict(self, scaled, prices_array, days_ahead):

        train_size = int(len(scaled) * 0.80)
        train_data = scaled[:train_size]
        test_data  = scaled[train_size - self.sequence_length:]

        X_train, y_train = self._prepare_sequences(train_data)
        X_test,  y_test  = self._prepare_sequences(test_data)

        X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
        X_test  = X_test.reshape(X_test.shape[0],  X_test.shape[1],  1)

        model = self._build_lstm_model((self.sequence_length, 1))

        early_stop = EarlyStopping(
            monitor="val_loss", patience=5, restore_best_weights=True)

        model.fit(
            X_train, y_train,
            epochs=50,
            batch_size=32,
            validation_split=0.1,
            callbacks=[early_stop],
            verbose=0
        )
        self.model = model
        self.is_trained = True

        test_pred_scaled = model.predict(X_test, verbose=0)
        test_predicted = self.scaler.inverse_transform(test_pred_scaled).flatten()
        test_actual    = self.scaler.inverse_transform(
            y_test.reshape(-1, 1)).flatten()

        last_sequence = scaled[-self.sequence_length:].copy()
        future_preds = []

        for _ in range(days_ahead):
            seq = last_sequence.reshape(1, self.sequence_length, 1)
            next_scaled = model.predict(seq, verbose=0)[0, 0]

            next_price = self.scaler.inverse_transform([[next_scaled]])[0, 0]
            future_preds.append(next_price)

            last_sequence = np.append(last_sequence[1:], [[next_scaled]], axis=0)

        metrics = self._calc_metrics(test_actual, test_predicted,
                                     float(prices_array[-1]))
        return np.array(future_preds), test_actual, test_predicted, metrics

    def _calc_metrics(self, actual, predicted, current_price):
        mse  = mean_squared_error(actual, predicted)
        mae  = mean_absolute_error(actual, predicted)
        rmse = np.sqrt(mse)

        mape = np.mean(np.abs((actual - predicted) / (actual + 1e-10))) * 100
        accuracy = max(0, 100 - mape)

        return {
            "rmse": round(float(rmse), 2),
            "mae":  round(float(mae), 2),
            "mape_pct": round(float(mape), 2),
            "accuracy_pct": round(float(accuracy), 2),
            "interpretation": (
                f"On test data, predictions were off by Rs.{mae:.2f} on average "
                f"({mape:.1f}% error). Model accuracy: {accuracy:.1f}%"
            )
        }

    def _generate_chart(self, symbol, close, dates, predictions, days_ahead):
        fig, ax = plt.subplots(figsize=(13, 6))
        fig.patch.set_facecolor(DARK)
        ax.set_facecolor(CARD)

        hist_days = min(180, len(close))
        hist_close = close.iloc[-hist_days:]
        hist_dates = dates[-hist_days:]

        ax.plot(hist_dates, hist_close.values,
                color=ACCENT, linewidth=1.8, label="Historical Price")

        ma20 = hist_close.rolling(20).mean()
        ax.plot(hist_dates, ma20.values,
                color=GOLD, linewidth=1, linestyle="--",
                alpha=0.8, label="20-day MA")

        import pandas as _pd
        last_date = dates[-1]
        future_dates = _pd.bdate_range(
            start=last_date, periods=days_ahead + 1)[1:]

        connect_prices = [float(close.iloc[-1])] + list(predictions)
        connect_dates  = [last_date] + list(future_dates)

        ax.plot(connect_dates, connect_prices,
                color=GOLD, linewidth=2, linestyle="--",
                marker="o", markersize=5, label=f"{days_ahead}-day Forecast")

        upper = [p * 1.02 for p in connect_prices]
        lower = [p * 0.98 for p in connect_prices]
        ax.fill_between(connect_dates, lower, upper,
                        alpha=0.15, color=GOLD, label="±2% Uncertainty Band")

        ax.axvline(x=last_date, color=TEXT,
                   linewidth=1, linestyle=":", alpha=0.5)
        ax.text(last_date, ax.get_ylim()[0],
                " Today", color=TEXT, fontsize=8, va="bottom")

        ax.set_title(f"{symbol} — Price Prediction ({days_ahead}-Day Forecast)",
                     color=TEXT, fontsize=13, fontweight="bold")
        ax.set_ylabel("Price (Rs.)", color=TEXT, fontsize=9)
        ax.tick_params(colors=TEXT, labelsize=8)
        ax.legend(facecolor=CARD, labelcolor=TEXT, fontsize=8, loc="upper left")
        ax.grid(True, color=GRID, alpha=0.4, linewidth=0.5)
        for sp in ax.spines.values():
            sp.set_color(GRID)

        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        fig.autofmt_xdate(rotation=25)
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150,
                    bbox_inches="tight", facecolor=DARK)
        buf.seek(0)
        plt.close(fig)
        return base64.b64encode(buf.read()).decode("utf-8")

    def _interpret(self, symbol, current, predictions,
                   metrics, change_pct):
        direction = "rise" if change_pct > 0 else "fall"
        strength  = ("strongly" if abs(change_pct) > 3
                     else "moderately" if abs(change_pct) > 1
                     else "slightly")
        return (
            f"The LSTM model predicts {symbol} will {strength} {direction} "
            f"by {abs(change_pct):.2f}% over the next 7 trading days, "
            f"from Rs.{current:,.2f} to Rs.{float(predictions[-1]):,.2f}. "
            f"Model accuracy on historical test data: "
            f"{metrics['accuracy_pct']:.1f}% "
            f"(average error: Rs.{metrics['mae']:.2f}). "
            f"Always combine with fundamental analysis and current news."
  )
