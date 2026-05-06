import httpx
import asyncio
from typing import Dict, Optional

LANGUAGES = {
    "english":  {"name": "English",  "code": "en", "flag": "🇬🇧"},
    "hindi":    {"name": "Hindi",    "code": "hi", "flag": "🇮🇳"},
    "tamil":    {"name": "Tamil",    "code": "ta", "flag": "🇮🇳"},
    "telugu":   {"name": "Telugu",   "code": "te", "flag": "🇮🇳"},
    "bengali":  {"name": "Bengali",  "code": "bn", "flag": "🇮🇳"},
    "marathi":  {"name": "Marathi",  "code": "mr", "flag": "🇮🇳"},
    "gujarati": {"name": "Gujarati", "code": "gu", "flag": "🇮🇳"},
    "kannada":  {"name": "Kannada",  "code": "kn", "flag": "🇮🇳"},
}

TEMPLATES = {

    "rsi_overbought": {
        "english":
            "⚠️ This stock looks EXPENSIVE right now.\n"
            "Imagine 100 people trading this stock — {rsi:.0f} of them are BUYING.\n"
            "That's too many buyers! The price has gone up too fast.\n"
            "💡 What to do: WAIT before buying. Price might come down soon.\n"
            "If you already own it, you might consider selling some.",

        "hindi":
            "⚠️ यह शेयर अभी MAHANGA (महंगा) लग रहा है!\n"
            "सोचो 100 लोग इसे खरीद-बेच रहे हैं — {rsi:.0f} लोग खरीद रहे हैं।\n"
            "इतने सारे लोग खरीद रहे हैं मतलब दाम ऊपर बहुत तेज़ गया है।\n"
            "💡 क्या करें: अभी मत खरीदो। थोड़ा इंतज़ार करो।\n"
            "अगर पहले से है तो थोड़ा बेच सकते हो।",

        "tamil":
            "⚠️ இந்த பங்கு இப்போது விலை அதிகமாக உள்ளது!\n"
            "100 பேர் வர்த்தகம் செய்தால் {rsi:.0f} பேர் வாங்குகிறார்கள்.\n"
            "இது மிகவும் அதிகம் — விலை வேகமாக ஏறியது.\n"
            "💡 என்ன செய்வது: இப்போது வாங்காதே. கொஞ்சம் காத்திரு.\n"
            "விலை கீழே வரலாம்.",

        "telugu":
            "⚠️ ఈ స్టాక్ ఇప్పుడు చాలా EXPENSIVE గా ఉంది!\n"
            "100 మంది ట్రేడ్ చేస్తే {rsi:.0f} మంది కొంటున్నారు.\n"
            "ఇది చాలా ఎక్కువ — ధర చాలా వేగంగా పెరిగింది.\n"
            "💡 ఏమి చేయాలి: ఇప్పుడు కొనకు. కొంచెం వేచి ఉండు.",

        "bengali":
            "⚠️ এই শেয়ার এখন অনেক দামী!\n"
            "১০০ জন ট্রেড করলে {rsi:.0f} জন কিনছে।\n"
            "এত বেশি মানুষ কিনছে — দাম খুব দ্রুত বেড়েছে।\n"
            "💡 কী করবে: এখন কিনো না। একটু অপেক্ষা করো।",

        "marathi":
            "⚠️ हा शेअर आत्ता खूप महाग वाटतो!\n"
            "100 लोक ट्रेड करत असतील तर {rsi:.0f} जण विकत घेत आहेत.\n"
            "हे खूप जास्त आहे — भाव खूप वेगाने वाढला.\n"
            "💡 काय करावे: आत्ता विकत घेऊ नका. थोडी वाट पाहा.",

        "gujarati":
            "⚠️ આ સ્ટૉક હમણાં ઘણો મોઘો લાગે છે!\n"
            "100 લોકો ટ્રેડ કરે તો {rsi:.0f} લોકો ખરીદે છે.\n"
            "આ ઘણું વધારે છે — ભાવ ઝડપથી ઊંચો ગયો.\n"
            "💡 શું કરવું: અત્યારે ખરીદશો નહીં. થોડી રાહ જુઓ.",

        "kannada":
            "⚠️ ಈ ಸ್ಟಾಕ್ ಈಗ ತುಂಬಾ ದುಬಾರಿ ಆಗಿದೆ!\n"
            "100 ಜನ ಟ್ರೇಡ್ ಮಾಡಿದರೆ {rsi:.0f} ಜನ ಕೊಳ್ಳುತ್ತಿದ್ದಾರೆ.\n"
            "ಇದು ತುಂಬಾ ಹೆಚ್ಚು — ಬೆಲೆ ತ್ವರಿತವಾಗಿ ಏರಿತು.\n"
            "💡 ಏನು ಮಾಡಬೇಕು: ಈಗ ಕೊಳ್ಳಬೇಡ. ಸ್ವಲ್ಪ ಕಾಯು.",
    },

    "rsi_oversold": {
        "english":
            "🟢 This stock might be a BUYING OPPORTUNITY!\n"
            "Only {rsi:.0f} out of 100 traders are buying — most people are scared.\n"
            "When everyone is scared, prices get cheap.\n"
            "💡 What to do: This COULD be a good time to buy slowly.\n"
            "Don't put all your money at once. Buy in small amounts.",

        "hindi":
            "🟢 यह शेयर खरीदने का मौका हो सकता है!\n"
            "100 में से सिर्फ {rsi:.0f} लोग खरीद रहे हैं — बाकी सब डरे हुए हैं।\n"
            "जब सब डरते हैं, दाम सस्ता हो जाता है।\n"
            "💡 क्या करें: धीरे-धीरे थोड़ा-थोड़ा खरीदो।\n"
            "एक बार में सारा पैसा मत लगाओ।",

        "tamil":
            "🟢 இந்த பங்கு வாங்குவதற்கு நல்ல வாய்ப்பாக இருக்கலாம்!\n"
            "100 பேரில் {rsi:.0f} பேர் மட்டுமே வாங்குகிறார்கள்.\n"
            "எல்லோரும் பயப்படும்போது விலை குறைகிறது.\n"
            "💡 என்ன செய்வது: கொஞ்சம் கொஞ்சமாக வாங்கலாம்.",

        "telugu":
            "🟢 ఈ స్టాక్ కొనడానికి మంచి అవకాశం కావచ్చు!\n"
            "100 మంది లో {rsi:.0f} మంది మాత్రమే కొంటున్నారు.\n"
            "అందరూ భయపడినప్పుడు ధర తక్కువగా ఉంటుంది.\n"
            "💡 ఏమి చేయాలి: కొంచెం కొంచెం కొనవచ్చు.",

        "bengali":
            "🟢 এই শেয়ার কেনার ভালো সুযোগ হতে পারে!\n"
            "১০০ জনের মধ্যে মাত্র {rsi:.0f} জন কিনছে।\n"
            "যখন সবাই ভয় পায়, দাম সস্তা হয়।\n"
            "💡 কী করবে: অল্প অল্প করে কিনতে পারো।",

        "marathi":
            "🟢 हा शेअर विकत घेण्याची चांगली संधी असू शकते!\n"
            "100 पैकी फक्त {rsi:.0f} जण विकत घेत आहेत.\n"
            "सगळे घाबरतात तेव्हा भाव स्वस्त होतो.\n"
            "💡 काय करावे: थोडे थोडे विकत घ्या.",

        "gujarati":
            "🟢 આ સ્ટૉક ખરીદવાની સારી તક હોઈ શકે!\n"
            "100 માંથી ફક્ત {rsi:.0f} લોકો ખરીદે છે.\n"
            "જ્યારે બધા ડરે ત્યારે ભાવ સસ્તો થાય.\n"
            "💡 શું કરવું: થોડું થોડું ખરીદો.",

        "kannada":
            "🟢 ಈ ಸ್ಟಾಕ್ ಕೊಳ್ಳಲು ಉತ್ತಮ ಅವಕಾಶ ಇರಬಹುದು!\n"
            "100 ರಲ್ಲಿ ಕೇವಲ {rsi:.0f} ಜನ ಕೊಳ್ಳುತ್ತಿದ್ದಾರೆ.\n"
            "ಎಲ್ಲರೂ ಭಯಪಡುವಾಗ ಬೆಲೆ ಅಗ್ಗವಾಗುತ್ತದೆ.\n"
            "💡 ಏನು ಮಾಡಬೇಕು: ಸ್ವಲ್ಪ ಸ್ವಲ್ಪ ಕೊಳ್ಳಿ.",
    },

    "rsi_neutral": {
        "english":
            "😐 This stock is moving NORMALLY right now.\n"
            "RSI is {rsi:.0f} — neither too many buyers nor too many sellers.\n"
            "💡 What to do: Watch for a few more days before deciding.\n"
            "Check the company's recent news before buying.",

        "hindi":
            "😐 यह शेयर अभी सामान्य रूप से चल रहा है।\n"
            "RSI {rsi:.0f} है — न बहुत खरीदार, न बहुत बेचने वाले।\n"
            "💡 क्या करें: कुछ दिन और देखो। कंपनी की खबरें पढ़ो।",

        "tamil":
            "😐 இந்த பங்கு இப்போது சாதாரணமாக நகர்கிறது.\n"
            "RSI {rsi:.0f} — சமநிலையில் உள்ளது.\n"
            "💡 என்ன செய்வது: சில நாள் பார்த்திரு.",

        "telugu":
            "😐 ఈ స్టాక్ ఇప్పుడు సాధారణంగా కదులుతోంది.\n"
            "RSI {rsi:.0f} — సమతుల్యంగా ఉంది.\n"
            "💡 ఏమి చేయాలి: కొన్ని రోజులు చూడు.",

        "bengali":
            "😐 এই শেয়ার এখন স্বাভাবিকভাবে চলছে।\n"
            "RSI {rsi:.0f} — ভারসাম্যপূর্ণ।\n"
            "💡 কী করবে: কয়েকদিন দেখো।",

        "marathi":
            "😐 हा शेअर आत्ता सामान्यपणे चालत आहे।\n"
            "RSI {rsi:.0f} — संतुलित आहे।\n"
            "💡 काय करावे: काही दिवस बघा.",

        "gujarati":
            "😐 આ સ્ટૉક હમણાં સામાન્ય રીતે ચાલી રહ્યો છે.\n"
            "RSI {rsi:.0f} — સંતુલિત છે.\n"
            "💡 શું કરવું: થોડા દિવસ જુઓ.",

        "kannada":
            "😐 ಈ ಸ್ಟಾಕ್ ಈಗ ಸಾಮಾನ್ಯವಾಗಿ ಚಲಿಸುತ್ತಿದೆ.\n"
            "RSI {rsi:.0f} — ಸಮತೋಲನದಲ್ಲಿದೆ.\n"
            "💡 ಏನು ಮಾಡಬೇಕು: ಕೆಲವು ದಿನ ನೋಡಿ.",
    },

    "macd_bullish": {
        "english":
            "📈 GOOD SIGN — Stock momentum is turning POSITIVE!\n"
            "MACD crossed above the signal line.\n"
            "Think of it like a train starting to accelerate upward.\n"
            "💡 What to do: This is a potential BUY signal.\n"
            "But confirm with RSI and news before investing.",

        "hindi":
            "📈 अच्छा संकेत — शेयर ऊपर जाने की रफ़्तार पकड़ रहा है!\n"
            "MACD ने signal line को ऊपर से काटा।\n"
            "मतलब गाड़ी ऊपर की तरफ तेज़ होने लगी है।\n"
            "💡 क्या करें: यह खरीदने का संकेत हो सकता है।\n"
            "लेकिन पहले खबरें भी देखो।",

        "tamil":
            "📈 நல்ல அறிகுறி — பங்கு மேல்நோக்கி வேகம் எடுக்கிறது!\n"
            "MACD சிக்னல் லைனை கடந்தது.\n"
            "💡 என்ன செய்வது: இது வாங்கும் சமயமாக இருக்கலாம்.",

        "telugu":
            "📈 మంచి సంకేతం — స్టాక్ పైకి వేగం పుంజుకుంటోంది!\n"
            "MACD సిగ్నల్ లైన్ ని దాటింది.\n"
            "💡 ఏమి చేయాలి: ఇది కొనే సంకేతం కావచ్చు.",

        "bengali":
            "📈 ভালো লক্ষণ — শেয়ার উপরের দিকে গতি নিচ্ছে!\n"
            "MACD সিগন্যাল লাইন অতিক্রম করেছে।\n"
            "💡 কী করবে: এটা কেনার সুযোগ হতে পারে।",

        "marathi":
            "📈 चांगले चिन्ह — शेअर वरच्या दिशेने वेग घेतोय!\n"
            "MACD ने signal line ओलांडली.\n"
            "💡 काय करावे: हे विकत घेण्याचे संकेत असू शकते.",

        "gujarati":
            "📈 સારી નિશાની — સ્ટૉક ઉપર ઝડપ પકડી રહ્યો છે!\n"
            "MACD સિગ્નલ લાઇન ઓળંગ્યો.\n"
            "💡 શું કરવું: આ ખરીદીની તક હોઈ શકે.",

        "kannada":
            "📈 ಒಳ್ಳೆಯ ಸಂಕೇತ — ಸ್ಟಾಕ್ ಮೇಲ್ಮುಖ ವೇಗ ಪಡೆಯುತ್ತಿದೆ!\n"
            "MACD ಸಿಗ್ನಲ್ ಲೈನ್ ದಾಟಿದೆ.\n"
            "💡 ಏನು ಮಾಡಬೇಕು: ಇದು ಖರೀದಿ ಸಂಕೇತ ಆಗಿರಬಹುದು.",
    },

    "macd_bearish": {
        "english":
            "📉 WARNING — Stock momentum is turning NEGATIVE!\n"
            "MACD crossed below the signal line.\n"
            "Like a car starting to brake — price may fall further.\n"
            "💡 What to do: Be careful. Avoid buying right now.\n"
            "If you own this stock, consider setting a stop loss.",

        "hindi":
            "📉 सावधान — शेयर नीचे जाने की रफ़्तार पकड़ रहा है!\n"
            "MACD नीचे से signal line को काटा।\n"
            "मतलब गाड़ी ब्रेक लग रहे हैं — दाम और गिर सकता है।\n"
            "💡 क्या करें: अभी मत खरीदो।\n"
            "अगर पहले से है तो stop loss लगा लो।",

        "tamil":
            "📉 எச்சரிக்கை — பங்கு கீழ்நோக்கி போகிறது!\n"
            "MACD சிக்னல் லைனுக்கு கீழே சென்றது.\n"
            "💡 என்ன செய்வது: இப்போது வாங்காதே. கவனமாக இரு.",

        "telugu":
            "📉 హెచ్చరిక — స్టాక్ కిందికి వెళ్తోంది!\n"
            "MACD సిగ్నల్ లైన్ కింద వెళ్ళింది.\n"
            "💡 ఏమి చేయాలి: ఇప్పుడు కొనకు. జాగ్రత్తగా ఉండు.",

        "bengali":
            "📉 সতর্কতা — শেয়ার নিচের দিকে যাচ্ছে!\n"
            "MACD সিগন্যাল লাইনের নিচে গেছে।\n"
            "💡 কী করবে: এখন কিনো না। সাবধান থাকো।",

        "marathi":
            "📉 सावधानी — शेअर खाली जात आहे!\n"
            "MACD signal line खाली गेला.\n"
            "💡 काय करावे: आत्ता विकत घेऊ नका.",

        "gujarati":
            "📉 સાવચેત — સ્ટૉક નીચે જઈ રહ્યો છે!\n"
            "MACD સિગ્નલ લાઇન નીચે ગયો.\n"
            "💡 શું કરવું: અત્યારે ખરીદશો નહીં.",

        "kannada":
            "📉 ಎಚ್ಚರಿಕೆ — ಸ್ಟಾಕ್ ಕೆಳಗೆ ಹೋಗುತ್ತಿದೆ!\n"
            "MACD ಸಿಗ್ನಲ್ ಲೈನ್ ಕೆಳಗೆ ಹೋಯಿತು.\n"
            "💡 ಏನು ಮಾಡಬೇಕು: ಈಗ ಕೊಳ್ಳಬೇಡ.",
    },

    "overall_buy": {
        "english":
            "✅ OVERALL: Looks like a POTENTIAL BUY\n"
            "Multiple signals are pointing UP for {symbol}.\n"
            "📌 Suggested action: You can start buying SMALL amounts.\n"
            "Don't invest more than 5-10% of your savings in one stock.\n"
            "⚠️ Remember: No prediction is 100% correct. Markets can surprise.",

        "hindi":
            "✅ कुल मिलाकर: {symbol} खरीदने का संकेत दिख रहा है!\n"
            "कई indicators ऊपर की तरफ इशारा कर रहे हैं।\n"
            "📌 सुझाव: थोड़ा-थोड़ा खरीदना शुरू करो।\n"
            "अपनी बचत का 5-10% से ज़्यादा एक शेयर में मत लगाओ।\n"
            "⚠️ याद रहे: कोई भी prediction 100% सही नहीं होती।",

        "tamil":
            "✅ மொத்தத்தில்: {symbol} வாங்கலாம் என்று தெரிகிறது!\n"
            "பல சமிக்ஞைகள் மேல்நோக்கி உள்ளன.\n"
            "📌 ஆலோசனை: கொஞ்சம் கொஞ்சமாக வாங்கலாம்.\n"
            "⚠️ எந்த கணிப்பும் 100% சரியானதல்ல.",

        "telugu":
            "✅ మొత్తంగా: {symbol} కొనవచ్చు అని కనిపిస్తోంది!\n"
            "చాలా సంకేతాలు పైకి చూపిస్తున్నాయి.\n"
            "📌 సలహా: కొంచెం కొంచెం కొనడం మొదలు పెట్టవచ్చు.\n"
            "⚠️ ఏ అంచనా కూడా 100% సరైనది కాదు.",

        "bengali":
            "✅ সামগ্রিকভাবে: {symbol} কেনার সংকেত দেখাচ্ছে!\n"
            "একাধিক সংকেত উপরের দিকে।\n"
            "📌 পরামর্শ: অল্প অল্প করে কিনতে পারো।\n"
            "⚠️ কোনো পূর্বাভাস ১০০% সঠিক নয়।",

        "marathi":
            "✅ एकूणच: {symbol} विकत घेण्याचे संकेत दिसत आहेत!\n"
            "अनेक indicators वरच्या दिशेने आहेत.\n"
            "📌 सल्ला: थोडे थोडे विकत घेणे सुरू करा.\n"
            "⚠️ कोणतेही prediction 100% बरोबर नसते.",

        "gujarati":
            "✅ એકંદરે: {symbol} ખરીદવાના સંકેત દેખાય છે!\n"
            "ઘણા indicators ઉપર છે.\n"
            "📌 સૂચન: થોડું થોડું ખરીદવાનું શરૂ કરો.\n"
            "⚠️ કોઈ prediction 100% સાચી નથી.",

        "kannada":
            "✅ ಒಟ್ಟಾರೆ: {symbol} ಕೊಳ್ಳುವ ಸಂಕೇತ ಕಾಣಿಸುತ್ತಿದೆ!\n"
            "ಅನೇಕ indicators ಮೇಲ್ಮುಖವಾಗಿವೆ.\n"
            "📌 ಸಲಹೆ: ಸ್ವಲ್ಪ ಸ್ವಲ್ಪ ಕೊಳ್ಳಲು ಶುರು ಮಾಡಿ.\n"
            "⚠️ ಯಾವ prediction ಕೂಡ 100% ಸರಿಯಲ್ಲ.",
    },

    "overall_sell": {
        "english":
            "🔴 OVERALL: CAUTION — Not a good time to buy {symbol}\n"
            "Multiple signals pointing DOWN.\n"
            "📌 Suggested action: Stay away for now. Watch for a few weeks.\n"
            "If you own this stock, set a stop loss to protect yourself.\n"
            "⚠️ Never panic sell — have a plan before investing.",

        "hindi":
            "🔴 कुल मिलाकर: {symbol} अभी खरीदना ठीक नहीं\n"
            "कई indicators नीचे की तरफ इशारा कर रहे हैं।\n"
            "📌 सुझाव: अभी दूर रहो। कुछ हफ्ते बाद देखो।\n"
            "अगर पहले से है तो stop loss लगा लो।\n"
            "⚠️ घबराकर मत बेचो — पहले से plan बनाओ।",

        "tamil":
            "🔴 மொத்தத்தில்: {symbol} இப்போது வாங்கவேண்டாம்\n"
            "பல சமிக்ஞைகள் கீழ்நோக்கி உள்ளன.\n"
            "📌 ஆலோசனை: சில வாரங்கள் காத்திரு.\n"
            "⚠️ பதட்டத்தில் விற்காதே.",

        "telugu":
            "🔴 మొత్తంగా: {symbol} ఇప్పుడు కొనడం మంచిది కాదు\n"
            "చాలా సంకేతాలు కిందికి చూపిస్తున్నాయి.\n"
            "📌 సలహా: కొన్ని వారాలు చూడు.\n"
            "⚠️ భయంతో అమ్మకు.",

        "bengali":
            "🔴 সামগ্রিকভাবে: {symbol} এখন কেনা ঠিক না\n"
            "একাধিক সংকেত নিচের দিকে।\n"
            "📌 পরামর্শ: কয়েক সপ্তাহ দেখো।\n"
            "⚠️ আতঙ্কে বিক্রি করো না।",

        "marathi":
            "🔴 एकूणच: {symbol} आत्ता विकत घेणे योग्य नाही\n"
            "अनेक indicators खाली आहेत.\n"
            "📌 सल्ला: काही आठवडे बघा.\n"
            "⚠️ घाबरून विकू नका.",

        "gujarati":
            "🔴 એકંદરે: {symbol} અત્યારે ખરીદવું યોગ્ય નથી\n"
            "ઘણા indicators નીચે છે.\n"
            "📌 સૂચન: થોડા અઠવાડિયા જુઓ.\n"
            "⚠️ ગભરાઈને વેચશો નહીં.",

        "kannada":
            "🔴 ಒಟ್ಟಾರೆ: {symbol} ಈಗ ಕೊಳ್ಳುವುದು ಸರಿಯಲ್ಲ\n"
            "ಅನೇಕ indicators ಕೆಳಮುಖವಾಗಿವೆ.\n"
            "📌 ಸಲಹೆ: ಕೆಲವು ವಾರ ನೋಡಿ.\n"
            "⚠️ ಭಯದಿಂದ ಮಾರಬೇಡ.",
    },

    "crypto_up": {
        "english":
            "🚀 {symbol} is trending UP today!\n"
            "Price in India: Rs.{price:,.0f}\n"
            "24h change: {change:+.1f}%\n\n"
            "📌 Remember India's crypto tax rules:\n"
            "• 30% flat tax on ALL crypto profits (no slab benefit)\n"
            "• 1% TDS on every transaction above Rs.10,000\n"
            "• Losses CANNOT be set off against gains\n"
            "💡 Invest only what you can afford to lose completely.",

        "hindi":
            "🚀 {symbol} आज ऊपर जा रहा है!\n"
            "भारत में दाम: Rs.{price:,.0f}\n"
            "24 घंटे में बदलाव: {change:+.1f}%\n\n"
            "📌 भारत में crypto tax याद रखो:\n"
            "• सभी मुनाफे पर 30% टैक्स\n"
            "• Rs.10,000 से ऊपर हर लेनदेन पर 1% TDS\n"
            "• घाटा दूसरे फायदे से नहीं काट सकते\n"
            "💡 सिर्फ वो पैसा लगाओ जो डूब जाए तो भी चले।",

        "tamil":
            "🚀 {symbol} இன்று மேலே போகிறது!\n"
            "இந்தியாவில் விலை: Rs.{price:,.0f}\n"
            "24 மணி நேர மாற்றம்: {change:+.1f}%\n\n"
            "📌 இந்தியாவில் crypto வரி:\n"
            "• அனைத்து லாபத்திலும் 30% வரி\n"
            "• Rs.10,000 மேல் 1% TDS\n"
            "💡 இழந்தாலும் பரவாயில்லை என்ற பணத்தை மட்டும் போடு.",

        "telugu":
            "🚀 {symbol} ఈరోజు పైకి వెళ్తోంది!\n"
            "భారతదేశంలో ధర: Rs.{price:,.0f}\n"
            "24 గంటల మార్పు: {change:+.1f}%\n\n"
            "📌 భారతదేశంలో crypto పన్ను:\n"
            "• అన్ని లాభాలపై 30% పన్ను\n"
            "• Rs.10,000 పైన 1% TDS\n"
            "💡 పోయినా ఫర్వాలేదు అనే డబ్బే పెట్టు.",

        "bengali":
            "🚀 {symbol} আজ উপরে যাচ্ছে!\n"
            "ভারতে দাম: Rs.{price:,.0f}\n"
            "২৪ ঘণ্টার পরিবর্তন: {change:+.1f}%\n\n"
            "📌 ভারতে crypto ট্যাক্স:\n"
            "• সব লাভে ৩০% ট্যাক্স\n"
            "• Rs.১০,০০০ এর উপরে ১% TDS\n"
            "💡 হারালেও ক্ষতি নেই এমন টাকাই বিনিয়োগ করো।",

        "marathi":
            "🚀 {symbol} आज वर जात आहे!\n"
            "भारतात दर: Rs.{price:,.0f}\n"
            "24 तासातील बदल: {change:+.1f}%\n\n"
            "📌 भारतात crypto कर:\n"
            "• सर्व नफ्यावर 30% कर\n"
            "• Rs.10,000 वर 1% TDS\n"
            "💡 गेले तरी चालेल असेच पैसे गुंतवा.",

        "gujarati":
            "🚀 {symbol} આજે ઉપર જઈ રહ્યો છે!\n"
            "ભારતમાં ભાવ: Rs.{price:,.0f}\n"
            "24 કલાકનો ફેરફાર: {change:+.1f}%\n\n"
            "📌 ભારતમાં crypto ટૅક્સ:\n"
            "• બધા નફા પર 30% ટૅક્સ\n"
            "• Rs.10,000 ઉપર 1% TDS\n"
            "💡 ગુમાવ્યે ચાલે એટલા જ પૈસા રોકો.",

        "kannada":
            "🚀 {symbol} ಇಂದು ಮೇಲೆ ಹೋಗುತ್ತಿದೆ!\n"
            "ಭಾರತದಲ್ಲಿ ಬೆಲೆ: Rs.{price:,.0f}\n"
            "24 ಗಂಟೆ ಬದಲಾವಣೆ: {change:+.1f}%\n\n"
            "📌 ಭಾರತದಲ್ಲಿ crypto ತೆರಿಗೆ:\n"
            "• ಎಲ್ಲಾ ಲಾಭದ ಮೇಲೆ 30% ತೆರಿಗೆ\n"
            "• Rs.10,000 ಮೇಲೆ 1% TDS\n"
            "💡 ಕಳೆದರೂ ಪರವಾಗಿಲ್ಲ ಎಂಬ ಹಣವನ್ನೇ ಹಾಕು.",
    },
}

class MultiLangExplainer:

    def explain_stock(
        self,
        symbol: str,
        rsi: float,
        macd_signal: str,
        overall: str,
        price: float,
        change_pct: float,
        language: str = "english"
    ) -> Dict:
        lang = language.lower()
        if lang not in LANGUAGES:
            lang = "english"

        explanations = {}

        if rsi >= 70:
            rsi_key = "rsi_overbought"
        elif rsi <= 30:
            rsi_key = "rsi_oversold"
        else:
            rsi_key = "rsi_neutral"

        rsi_template = TEMPLATES[rsi_key].get(lang, TEMPLATES[rsi_key]["english"])
        explanations["rsi"] = rsi_template.format(rsi=rsi, symbol=symbol)

        macd_key = f"macd_{macd_signal}"
        if macd_key in TEMPLATES:
            macd_template = TEMPLATES[macd_key].get(lang, TEMPLATES[macd_key]["english"])
            explanations["macd"] = macd_template.format(symbol=symbol)

        overall_key = f"overall_{overall}"
        if overall_key in TEMPLATES:
            overall_template = TEMPLATES[overall_key].get(lang, TEMPLATES[overall_key]["english"])
            explanations["overall"] = overall_template.format(symbol=symbol)

        return {
            "symbol":      symbol,
            "language":    LANGUAGES[lang]["name"],
            "flag":        LANGUAGES[lang]["flag"],
            "rsi_value":   round(rsi, 1),
            "explanations": explanations,
            "all_languages": list(LANGUAGES.keys()),
        }

    def explain_crypto(
        self,
        symbol: str,
        price_inr: float,
        change_24h: float,
        language: str = "english"
    ) -> Dict:
        lang = language.lower()
        if lang not in LANGUAGES:
            lang = "english"

        direction = "up" if change_24h >= 0 else "down"
        template_key = f"crypto_{direction}"

        if template_key in TEMPLATES:
            template = TEMPLATES[template_key].get(lang, TEMPLATES[template_key]["english"])
            explanation = template.format(
                symbol=symbol,
                price=price_inr,
                change=change_24h
            )
        else:
            explanation = f"{symbol}: Rs.{price_inr:,.0f} ({change_24h:+.1f}%)"

        return {
            "symbol":      symbol,
            "language":    LANGUAGES[lang]["name"],
            "flag":        LANGUAGES[lang]["flag"],
            "price_inr":   round(price_inr, 2),
            "change_24h":  round(change_24h, 2),
            "explanation": explanation,
            "all_languages": list(LANGUAGES.keys()),
        }

    async def explain_with_ollama(
        self,
        context: str,
        language: str = "hindi"
    ) -> str:
      lang_name = LANGUAGES.get(language, {}).get("name", "Hindi")

        prompt = (
            f"Explain the following stock market information to a complete beginner "
            f"in {lang_name}. Use very simple words. Use an analogy they can relate to "
            f"(like cricket, farming, or daily life in India). Keep it under 5 lines.\n\n"
            f"Information: {context}"
        )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": "qwen2.5:7b",
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "options": {"temperature": 0.7, "num_predict": 200}
                    }
                )
                return r.json()["message"]["content"]
        except Exception:

            return f"[Ollama not running — using template]\n{context}"

explainer = MultiLangExplainer()
