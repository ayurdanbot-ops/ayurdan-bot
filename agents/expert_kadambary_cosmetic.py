from google import genai
from google.genai import types

EXPERT_KNOWLEDGE = """
📞 ടെലി-കോളർ സ്ക്രിപ്റ്റ് – ഡാൻഡ്രഫ് (തലയിലെ പൊടി പ്രശ്നം)
ആമുഖം (Introduction):
“നമസ്കാരം, ഞാൻ Ayurdan Ayurveda Hospitalൽ നിന്ന് സംസാരിക്കുന്നു. ഞാൻ ___ ആണ്. നിങ്ങൾക്ക് 2 മിനിറ്റ് സമയം ഉണ്ടോ?”
പ്രശ്നം തിരിച്ചറിയൽ (Problem Identification):
“താങ്കൾക്ക് തലയിലെ പൊടി (dandruff), ചൊറിച്ചിൽ, അല്ലെങ്കിൽ മുടി കൊഴിച്ചിൽ പോലുള്ള പ്രശ്നങ്ങൾ ഉണ്ടോ?”
(ഉണ്ടെങ്കിൽ തുടരണം)
“എത്ര കാലമായി ഈ പ്രശ്നം അനുഭവപ്പെടുന്നു?”
“ചൊറിച്ചിൽ കൂടിയുണ്ടോ?”
“മുടി കൊഴിച്ചിൽ ഉണ്ടോ?”
“നിങ്ങൾ ഇതിനായി മുമ്പ് എന്തെങ്കിലും ചികിത്സ എടുത്തിട്ടുണ്ടോ?”
അറിവ് നൽകൽ (Education / Awareness):
“ഡാൻഡ്രഫ് സാധാരണ പ്രശ്നമാണെങ്കിലും, ശരിയായ ചികിത്സ ലഭിക്കാത്ത പക്ഷം അത് മുടി കൊഴിച്ചിലിനും തലച്ചർമത്തിലെ മറ്റ് പ്രശ്നങ്ങൾക്കും കാരണമാകാം.”
“ആയുര്‍വേദത്തിൽ ഇത് ‘Darunaka’ എന്ന പേരിൽ അറിയപ്പെടുന്നു, ഇത് പ്രധാനമായും വാത-കഫ ദോഷങ്ങളുടെ അസന്തുലിതാവസ്ഥ മൂലമാണ് ഉണ്ടാകുന്നത്.”
പരിഹാരം അവതരിപ്പിക്കൽ (Solution Pitch):
“ഞങ്ങളുടെ Ayurdan Ayurveda Hospitalൽ, പൂർണ്ണമായും പ്രകൃതിദത്തമായ ആയുര്‍വേദ ചികിത്സകളാണ് നൽകുന്നത്.”
“ഇതിന് പ്രത്യേകമായ oil therapy, herbal medicines, diet & lifestyle guidance എന്നിവയിലൂടെ നമുക്ക് സ്ഥിരമായ പരിഹാരം ലഭിക്കാം.”
“Side effects ഒന്നും ഇല്ലാത്തതും, root cause address ചെയ്യുന്നതുമാണ് ഞങ്ങളുടെ ചികിത്സ.”
Call to Action (Appointment Fixing):
“നിങ്ങൾക്ക് ഒരു consultation book ചെയ്യാമോ?”
“Doctor consultation available ആണ്. നിങ്ങൾക്ക് hospital visit ചെയ്യാമോ, അല്ലെങ്കിൽ online consultation വേണോ?”
Closure (Ending):
“നന്ദി. കൂടുതൽ വിവരങ്ങൾക്ക് ഞങ്ങളെ ബന്ധപ്പെടാം. നിങ്ങളുടെ ആരോഗ്യം ഞങ്ങൾക്ക് പ്രധാനമാണ്.”
✅ Short Closing Line Options:
“നിങ്ങളുടെ മുടി ആരോഗ്യം സംരക്ഷിക്കാൻ ഇന്ന് തന്നെ ആരംഭിക്കൂ.”
“Natural ആയ ചികിത്സയിലൂടെ dandruff പൂര്‍ണമായി നിയന്ത്രിക്കാം.”

മുടി കൊഴിച്ചിൽ
ആമുഖം (Warm Opening):
“നമസ്കാരം… Ayurdan Ayurveda Hospitalൽ നിന്ന് ആണ് വിളിക്കുന്നത്. ഞാൻ ___ ആണ് സംസാരിക്കുന്നത്. ഇപ്പോൾ സംസാരിക്കാൻ സുഖമാണോ?”
ബന്ധം സൃഷ്ടിക്കൽ (Emotional Connection):
“ഒരു ചെറിയ ചോദ്യം ചോദിക്കട്ടെ…
ഇപ്പോൾ നിങ്ങൾക്ക് മുടി കൊഴിച്ചിൽ കാരണം അല്പം വിഷമമുണ്ടോ…?”
(കാത്തിരിക്കുക, patient സംസാരിക്കാൻ സമയം കൊടുക്കുക)
“മിക്ക ആളുകളും ഇതേ കാര്യം പറഞ്ഞുകൊണ്ടാണ് ഞങ്ങളെ സമീപിക്കുന്നത്…
മുടി കൊഴിയുമ്പോൾ, അത് ശരീരപ്രശ്നം മാത്രമല്ല, confidence-നെയും ബാധിക്കും… ശരിയാണോ?”
പ്രശ്നം മനസ്സിലാക്കൽ (Understanding the Pain):
“എത്ര കാലമായി ഇത് ശ്രദ്ധിക്കുന്നുണ്ട്?”
“മുടി comb ചെയ്യുമ്പോഴും wash ചെയ്യുമ്പോഴും കൂടുതലായി കൊഴിയുന്നുണ്ടോ?”
“മുമ്പ് ചികിത്സ എടുത്തിട്ടുണ്ടെങ്കിലും മാറ്റം കുറവാണോ?”
“ഇത് കൊണ്ട് നിങ്ങൾക്ക് tension അല്ലെങ്കിൽ stress കൂടുന്നുണ്ടോ…?”
ആശ്വാസവും വിശ്വാസവും (Reassurance):
“ഞാൻ പറയുന്നത് നിങ്ങളെ ആശ്വസിപ്പിക്കാൻ തന്നെയാണ്…
ഈ പ്രശ്നത്തിന് ശരിയായ ചികിത്സ എടുത്താൽ മാറ്റം definitely കാണാം.”
“ആയുര്‍വേദത്തിൽ ഇത് ‘Khalitya’ എന്ന് പറയുന്നു…
ഇത് ശരീരത്തിനുള്ളിലെ imbalance ആണ് കാരണം… അതുകൊണ്ട് പുറമേ എന്തെങ്കിലും oil മാത്രം ഉപയോഗിച്ചാൽ മതി എന്നല്ല.”
പരിഹാരം – Care Approach (Solution with Care):
“ഞങ്ങളുടെ Ayurdan Ayurveda Hospitalൽ,
ഒരാളുടെ body type, കാരണം എന്നിവ നോക്കി വ്യക്തിഗതമായി treatment നൽകുന്നു.”
“Medicines മാത്രം അല്ല…
✔️ oil therapies
✔️ diet guidance
✔️ stress management
ഇവയെല്ലാം combine ചെയ്ത് നമുക്ക് നല്ലൊരു result നേടാം.”
Call to Action (Soft & Caring):
“നിങ്ങൾക്ക് താൽപര്യമുണ്ടെങ്കിൽ…
ഒരു doctor consultation fix ചെയ്യാം…
നിങ്ങൾക്ക് hospital വരാൻ സുഖമാണോ…
അല്ലെങ്കിൽ online ആയി consult ചെയ്യാമോ…?”
Closure (Comforting Ending):
“നിങ്ങൾ ഇത്രയും ദിവസമായി ഇതിനെ കൊണ്ട് വിഷമിച്ചിരിക്കാം…
പക്ഷേ ശരിയായ care കിട്ടിയാൽ മാറ്റം വരും.”
“ഞങ്ങൾ കൂടെ ഉണ്ടാകും…
നന്ദി 🙏”

മുടി വളർച്ച
ആമുഖം (Very Gentle Opening):
“നമസ്കാരം… Ayurdan Ayurveda Hospitalൽ നിന്ന് ആണ് വിളിക്കുന്നത്… ഞാൻ ___ ആണ് സംസാരിക്കുന്നത്…
ഇപ്പോൾ സംസാരിക്കാൻ ഒരു മിനിറ്റ് സമയം ഉണ്ടോ…?”
ബന്ധം സൃഷ്ടിക്കൽ (Real Emotional Connect):
“ഒരു കാര്യം സത്യമായി പറയാമോ…
മുടി മുൻപത്തെ പോലെ വളരുന്നില്ലെന്ന് തോന്നുമ്പോൾ… അത് ചെറിയ കാര്യമെന്നു തോന്നിച്ചാലും… ഉള്ളിൽ വളരെ വിഷമമുണ്ടാക്കുന്ന കാര്യമാണല്ലോ…?”
(അവരെ സംസാരിക്കാൻ അനുവദിക്കുക)
“മുടി കുറയുമ്പോൾ കണ്ണാടിയിൽ നോക്കാൻ പോലും പലർക്കും മടി തോന്നാറുണ്ട്…
confidence പോലും കുറയുന്നുണ്ടാകും… അത് നിങ്ങൾക്കും feel ചെയ്യുന്നുണ്ടോ…?”
അവരുടെ വേദന കേൾക്കൽ (Active Listening):
“എപ്പോഴാണ് നിങ്ങൾക്ക് ഇത് കൂടുതൽ ശ്രദ്ധയിൽ പെട്ടത്…?”
“മുൻപത്തെ പോലെ length കൂടുന്നില്ലേ…?”
“മുടി thin ആകുന്നുണ്ടോ… അല്ലെങ്കിൽ വളരുന്നതിന് മുമ്പേ കൊഴിയുന്നുണ്ടോ…?”
“ഇതിന് വേണ്ടി പലതും try ചെയ്തിട്ടുണ്ടെങ്കിലും…
തൃപ്തികരമായ മാറ്റം കിട്ടിയില്ലെന്നു തോന്നുന്നുണ്ടോ…?”
ആശ്വാസം നൽകൽ (Emotional Reassurance):
“ഞാൻ ഒരു കാര്യം ഉറപ്പായി പറയാം…
ഇത് നിങ്ങളൊറ്റയ്ക്ക് അനുഭവിക്കുന്ന പ്രശ്നമല്ല…”
“പലരും ഇതേ പ്രശ്നവുമായി വരുന്നു…
പക്ഷേ ശരിയായ രീതിയിൽ care കിട്ടിയാൽ മാറ്റം കാണാൻ സാധിക്കും…”
വിശ്വാസം + അറിവ് (Trust + Gentle Education):
“മുടി വളരാത്തത് പുറമേ കാണുന്ന പ്രശ്നം മാത്രമല്ല…
ശരീരത്തിനുള്ളിലെ imbalance ആണ് കാരണം…”
“ആയുര്‍വേദം അത് വളരെ gently ആയി correct ചെയ്യുന്നു…
അതുകൊണ്ടാണ് slow ആയാലും natural ആയ result കിട്ടുന്നത്…”
പരിഹാരം (Caring Solution Approach):
“ഞങ്ങളുടെ Ayurdan Ayurveda Hospitalൽ,
ഓരോരുത്തരെയും individual ആയി consider ചെയ്ത് treatment നൽകുന്നു…”
“Medicines മാത്രം അല്ല…
✔️ scalp nourish ചെയ്യുന്ന therapies
✔️ ശരീരത്തിന് പോഷണം നൽകുന്ന മരുന്നുകൾ
✔️ diet & lifestyle support
ഇവയെല്ലാം ചേർന്നാണ് മുടി വീണ്ടും healthy ആയി വളരാൻ സഹായിക്കുന്നത്…”
Hope Building (Very Important):
“നിങ്ങൾക്ക് ഇപ്പോൾ തോന്നുന്ന പോലെ hopeless situation അല്ല ഇത്…
ശരിയായ direction കിട്ടിയാൽ… धीरे धीरे മാറ്റം വരും…”
“ആ മാറ്റം കാണുമ്പോൾ… നിങ്ങൾക്ക് തന്നെ confidence തിരിച്ചു വരും…”
Call to Action (Soft & Respectful):
“നിങ്ങൾക്ക് താൽപര്യമുണ്ടെങ്കിൽ…
ഒരു doctor consultation arrange ചെയ്ത് നോക്കാമോ…?”
“നിങ്ങൾക്ക് hospital വരാൻ സുഖമാണോ…
അല്ലെങ്കിൽ വീട്ടിൽ ഇരുന്ന് online ആയി consult ചെയ്യാമോ…?”
Closure (Heartfelt Ending):
“നിങ്ങൾ ഇതിനെ കൊണ്ട് വിഷമിച്ചിട്ടുണ്ടെങ്കിൽ…
അത് ഞങ്ങൾ മനസ്സിലാക്കുന്നു…”
“നിങ്ങളുടെ മുടി മാത്രം അല്ല…
നിങ്ങളുടെ confidence തിരിച്ചു കൊണ്ടുവരാൻ ഞങ്ങൾ കൂടെയുണ്ട്…”
“നന്ദി… 🙏”
❤️ Deep Emotional Closing Lines:
“ഇന്ന് നിങ്ങൾ എടുക്കുന്ന ഒരു ചെറിയ തീരുമാനം… നാളെയുടെ ആത്മവിശ്വാസമാകും.”
“മുടി വീണ്ടും വളരുമ്പോൾ… നിങ്ങളിൽ ഒരു പുതിയ സന്തോഷം കാണാം.”
“You deserve to feel confident again…”

അലോപേഷ്യ (Alopecia)
ആമുഖം (Gentle Opening):
“നമസ്കാരം… Ayurdan Ayurveda Hospitalൽ നിന്ന് ആണ് വിളിക്കുന്നത്… ഞാൻ ___ ആണ് സംസാരിക്കുന്നത്…
ഇപ്പോൾ സംസാരിക്കാൻ സുഖമാണോ…?”
ബന്ധം സൃഷ്ടിക്കൽ (Sensitive Emotional Connect):
“ഒരു കാര്യമാണ് ചോദിക്കേണ്ടത്…
മുടിയിൽ patch ആയി കൊഴിയുന്നത് കാണുമ്പോൾ… അത് അല്പം ഭയവും വിഷമവും ഉണ്ടാക്കുന്ന കാര്യമാണല്ലോ…?”
(അവരെ സംസാരിക്കാൻ അനുവദിക്കുക)
“പലർക്കും ഇത് പെട്ടെന്ന് വന്നപ്പോള്‍… ‘എന്താണ് സംഭവിക്കുന്നത്’ എന്ന് പോലും മനസ്സിലാകാതെ tension ആയിരിക്കും…
നിങ്ങൾക്കും അങ്ങനെ തോന്നിയിട്ടുണ്ടോ…?”
പ്രശ്നം മനസ്സിലാക്കൽ (Understanding the Situation):
“എത്ര കാലമായി ഈ patch hair loss കാണുന്നു?”
“ഒരു ഭാഗത്തേ മാത്രമോ… അല്ലെങ്കിൽ പല സ്ഥലങ്ങളിലും ഉണ്ടാകുന്നുണ്ടോ?”
“മുമ്പ് ഏതെങ്കിലും treatment എടുത്തിട്ടുണ്ടോ?”
“Doctor പറഞ്ഞ diagnosis ‘alopecia’ ആണോ…?”
“ഇത് കൊണ്ട് പുറത്തേക്ക് പോകാനും, ആളുകളെ കാണാനും കുറച്ച് hesitation ഉണ്ടാകുന്നുണ്ടോ…?”
ആശ്വാസം (Emotional Reassurance):
“ഞാൻ ഒരു കാര്യം ഉറപ്പായി പറയാം…
ഇത് നിങ്ങൾ മാത്രം അനുഭവിക്കുന്ന പ്രശ്നമല്ല…”
“പല patients ഇതേ അവസ്ഥയിൽ തന്നെയാണ് ഞങ്ങളെ സമീപിക്കുന്നത്…
ആദ്യത്തിൽ പേടിയുണ്ടാകും… പക്ഷേ ശരിയായ care കിട്ടിയാൽ improvement കാണാം…”
വിശ്വാസം + അറിവ് (Trust + Simple Education):
“ആയുര്‍വേദത്തിൽ ഇത് ‘Indralupta’ എന്ന രീതിയിൽ വിവരിക്കുന്നു…”
“ഇത് scalp-ലുള്ള hair roots inactive ആകുന്നതുകൊണ്ടാണ്…
അതുകൊണ്ട് പുറമേ ointment മാത്രം ഉപയോഗിച്ചാൽ പോരാ…
body-യിലെ imbalance correct ചെയ്യേണ്ടതാണ്…”
പരിഹാരം (Holistic & Hopeful Approach):
“ഞങ്ങളുടെ Ayurdan Ayurveda Hospitalൽ,
ഓരോ patient നും individualized treatment ആണ് നൽകുന്നത്…”
✔️ Hair root activate ചെയ്യാൻ പ്രത്യേക therapies
✔️ Internal herbal medicines (body balance ചെയ്യാൻ)
✔️ Diet & lifestyle guidance
“ഇത് धीरे धीरे scalp revive ചെയ്ത്… വീണ്ടും hair growth തുടങ്ങാൻ സഹായിക്കും…”
Hope Building (Very Important):
“ഈ condition കണ്ടപ്പോൾ ‘മുടി വീണ്ടും വരുമോ?’ എന്ന doubt പലർക്കും ഉണ്ടാകും…”
“പക്ഷേ ശരിയായ സമയത്ത് treatment തുടങ്ങിയാൽ…
patch areas-ലും regrowth കാണാൻ കഴിയുന്ന കേസുകൾ നമ്മൾ കണ്ടിട്ടുണ്ട്…”
Call to Action (Soft & Caring):
“നിങ്ങൾക്ക് താൽപര്യമുണ്ടെങ്കിൽ…
ഒരു doctor consultation arrange ചെയ്ത് നോക്കാമോ…?”
“നിങ്ങൾക്ക് hospital വരാൻ സുഖമാണോ…
അല്ലെങ്കിൽ online consultation വേണോ…?”
Closure (Heartfelt Ending):
“ഇത് കൊണ്ട് നിങ്ങൾ mentally upset ആയിട്ടുണ്ടെങ്കിൽ… അത് സ്വാഭാവികമാണ്…”
“പക്ഷേ നിങ്ങൾ ഒറ്റയാളല്ല…
നിങ്ങൾക്ക് വീണ്ടും normal feel ചെയ്യാൻ ഞങ്ങൾ കൂടെയുണ്ട്…”
“നന്ദി… 🙏”
❤️ Deep Emotional Closing Lines:
“മുടി മാത്രം അല്ല… ആത്മവിശ്വാസം തിരിച്ചു കൊണ്ടുവരാനാണ് ഞങ്ങളുടെ ശ്രമം.”
“Hope ഉണ്ടെങ്കിൽ change വരും… ഞങ്ങൾ ആ hope നല്കാം.”
“You are not alone… we are here with you.”
"""
EXPERT_KNOWLEDGE = '''
Section 1: Causes of Hair Fall

Why does hair fall out excessively?
Hormonal imbalance, nutritional deficiency, dandruff, excessive stress, and genetics are the main causes.

How much daily hair fall is normal?
Normally, falling of 50 to 100 hairs is natural. Anything more than that should be noticed.

Why does hair fall after delivery?
This is caused by a sudden decrease in the estrogen hormone level in the body. This is temporary.

Does chlorine in water cause hair fall?
Yes, hard water and chlorine strip moisture from the hair, causing it to break.

Does wearing a helmet cause hair fall?
Sweat from wearing a helmet and tight pulling (traction) can cause hair fall.

Does anemia cause hair fall?
Yes, when hemoglobin in the blood decreases, the required oxygen does not reach the hair roots.

Do thyroid problems cause hair fall?
Yes, thyroid hormone imbalance causes hair to thin and fall out.

Does vitamin deficiency affect hair growth?
Yes, deficiency in Vitamin B12, D, Biotin, and Iron stops hair growth.

Does PCOD cause hair fall?
Yes, due to hormonal imbalance in women, this often causes a decrease in hair on the forehead.

Is excessive heat (Heat styling) bad for hair?
Yes, hair dryers and straightening destroy the protein structure of the hair.

Section 2: Ayurvedic Treatments at Ayurdan

What treatment is available at Ayurdan for hair fall?
Scalp cleansing procedures, massage using special medicated oils, and Shirodhara are available.

What is Shirodhara? Is it good for hair?
This is a method of pouring medicated oils in a continuous stream on the forehead. This is excellent for reducing stress and growing hair.

How is Takradhara beneficial for hair?
This is a continuous pouring using medicated buttermilk. It helps to remove dandruff and provides cooling to the head.

Does Ayurdan provide special medicines for hair growth?
Yes, the doctor will prescribe pure Ayurvedic medicines to be taken internally and applied externally.

How long after treatment will the results be seen?
Usually, hair fall reduces within one month, and new hair will grow within 3-4 months.

Will Nasyam help treat hair fall?
Yes, 'Nasyam', administering medicines through the nose, is an excellent method prescribed by Ayurveda to strengthen hair roots.

Are there side effects to the treatment at Ayurdan?
No, since natural herbs are used, there will be minimal risk.

Is there a treatment for baldness (Baldness)?
In cases where hair roots are not completely destroyed, it is possible to regrow hair through Ayurvedic treatment.

Is there a solution for a receding hairline?
Marma massage and Lepanams (pastes) at Ayurdan increase blood flow and boost hair growth on the forehead.

How to prevent split ends (Split ends)?
Ayurvedic hair packs (Thalam) that retain hair moisture are available at Ayurdan.

Section 3: Common Doubts and Market Questions (Common Q&A)

Will hair fall again after treatment?
If proper diet and hair care are continued, hair fall will not happen again.

Is taking a bath after applying oil good for hair?
Yes, oil massage is essential to increase blood flow in the scalp.

Which type of oil is good for hair?
Ayurdan's self-prepared, herb-rich hair oils are the most effective. (Ayurdan Hair care oil)

Will using shampoo increase hair fall?
Shampoos containing chemicals are harmful. Use herbal or mild shampoos.

Is protein necessary for hair growth?
Yes, hair is made of a protein called Keratin. Include eggs and legumes in your diet.

Is there a treatment to blacken gray hair?
There are effective methods in Ayurveda to prevent premature graying and maintain the natural color of the hair.

Is combing wet hair wrong?
Yes, hair roots are weak when wet, which causes hair to fall.

Is eating curry leaves good for hair?
Yes, the iron in curry leaves helps hair growth tremendously.

Does lack of sleep cause hair fall?
Yes, the body's regeneration happens during sleep. 7-8 hours of sleep is essential.

How much time is required for treatment at Ayurdan?
Each session can take from 45 minutes to 1.5 hours.

Will treatment be effective for those with hereditary baldness?
If treated early, the speed of hair fall can be reduced and existing hair can be preserved.

Does drinking water help hair growth?
Yes, to keep hair roots hydrated, you should drink at least 3 liters of water daily.

Is it true that hair will grow only if dandruff is managed?
Yes, hair roots cannot breathe in a scalp with dandruff, preventing growth.

Can Ayurvedic treatments be done on chemically treated hair?
Definitely, Ayurvedic treatments can recover hair damaged by chemicals.

Does tying hair up cause hair fall?
Tying it too tightly can cause hair roots to break.

Is excessive salt in food bad for hair?
Yes, excessive salt and spiciness can cause premature graying and hair fall.

Do we need to book in advance to visit Ayurdan?
Yes, it is better to call and book to ensure the doctor's availability.

How important is a scalp massage for hair growth?
Massaging the scalp with fingers for 5 minutes daily will help hair growth.

Should a special shampoo be used after treatment?
It is appropriate to use natural hair wash powders or shampoos provided by Ayurdan.

Can age-related hair fall be prevented?
Although age-related hair fall cannot be completely prevented, hair health can be maintained through proper care.

What is 'Shiroabhyangam'?
This is a special massage done on the head using medicated oils.

What does Ayurdan have to reduce mental stress?
Shirodhara and yoga instructions help reduce stress and improve hair growth.

What is the use of gooseberry for hair growth?
Vitamin C in gooseberry provides wonderful results in preventing hair fall.

What is the cost of hair fall treatment?
Treatments are available at affordable rates depending on the severity of the problem. Treatments are available starting from 1500 rupees.

Can I go to work after treatment?
Yes, the treatment will not affect normal daily routines.

Why does the thickness of the hair decrease?
Because the hair roots do not get enough nutrition and the follicles become smaller.

When should I see a doctor?
You should see a doctor immediately when there is sudden excessive hair fall or circular hair loss (Alopecia) on the head.

Does Ayurdan have online consultation?
Yes, those who cannot come in person can speak to the doctor online.

Is cold water or hot water better for washing hair?
Cold water or slightly warm water is always better for hair.

What tips can be given for hair growth?
Healthy food, daily scalp cleaning, accurate Ayurvedic care - this is the Ayurdan mantra.
'''

GLOBAL_HOSPITAL_INFO = """
STRICT LOCATION AND CONTACT RULES:
- Branches: We ONLY have one hospital, located in Pandalam. There are NO other branches anywhere else. Online consultation is available for those who cannot visit.
- Booking Number: For appointments, always provide this exact number: 9048502449.
- Official Address: Whenever a user asks for the location or address, you MUST output this exact text in English (do not translate the address):

Ayurdan Ayurveda Hospital And
Panchakarma Center,
Valiyakoikkal Temple Road,
Near Pandalam Palace Pandalam
Kerala State, India 689503

For Booking : 9048502449
"""

def process_request(text: str, parts: list = None, history_text: str = "", state_notes: str = "") -> str:
    client = genai.Client()
    model = 'gemini-3-flash-preview'

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_level='MINIMAL'),
        system_instruction=(
            """1. IDENTITY & PERSONA:
You are 'Ayur Care', the highly empathetic Senior Expert at Kadambary Beauty Clinic.
Zero Meta-Talk: NEVER output internal reasoning, 'Silent Processing', or 'Thinking'. The very first character of your output MUST be the actual conversational text meant for the patient.

2. STRICT FORMATTING & CONCISENESS:
No Labels: NEVER output structural labels like 'Awareness', 'Education', 'AEAC', or 'Closing' in any language.
Bolding: NEVER use double asterisks (**). ONLY use single asterisks (*) for WhatsApp bolding.
Concise Empathy (50% Rule): Be 50% more concise than a standard AI. Do not write long paragraphs. Answer ONLY the specific question asked using short, punchy sentences.

3. PACING & MEMORY (THE ONE QUESTION LIMIT):
The Limit: You are STRICTLY FORBIDDEN from asking more than one question in a single message. You must wait for the user to answer before asking the next.
Zero-Repeat Rule: Check chat history. NEVER ask for information (Age, Height, Weight, Symptoms) that the user has already provided.

4. LANGUAGE & TRANSLATION FIREWALL:
Strict Mirroring: Detect the exact language/script of the user's input and reply 100% in that native script.
Zero Script Mixing: Do NOT mix English and regional languages (like Malayalam) in the same message. Do not leak English terms unless it is a specific product/brand name.

5. THE GENDER BAN & INFERENCE:
NEVER use the word 'Gender' (or its translations) in any language.
Auto-Infer: If the user asks about female-specific conditions (e.g., PCOD, post-delivery) or treatments, silently infer they are female and DO NOT ask. Proceed straight to asking their age.
Mandatory Phrasing: If you cannot infer, use this exact phrasing translated into their language: 'To recommend the best treatment, please let me know your age and whether you are male or female.'

6. THE AEAC CONSULTATION CLOSING FRAMEWORK:
When responding to a condition, strictly structure your extremely concise message like this:
A - Awareness: Validate their struggle empathetically in one sentence.
E - Education: Gently escalate urgency (why they need clinical help now).
A - Authority: Explain how we treat it using exactly 3 punchy bullet points (•).
C - Closing (Appointment Focus): Confidently pivot to booking. E.g., 'Let's get you in front of our doctors. What date and time works best for your consultation?'

7. EMPATHY, NOT SYMPATHY:
You must strictly show professional EMPATHY, not emotional SYMPATHY.
Do NOT pity the patient. Never use words expressing sorrow, pity, or overly dramatic emotional distress (e.g., do not say "I feel so sorry for you", "That is terrible", or "Oh no").
Do validate their reality. Acknowledge their frustration or pain professionally ("I understand how difficult this condition can be..."), and immediately pivot to clinical confidence and authority ("...our expertise has equipped us to help you overcome this.").

Outcomes vary by patient condition and final guarantees are deferred to the human doctor.

You specialize in Cosmetic procedures and Hair Care."""
        ) + "\n\nOUR TREATMENTS:\n" + EXPERT_KNOWLEDGE + "\n\n" + GLOBAL_HOSPITAL_INFO + state_notes
    )

    contents = []
    if parts:
        contents.extend(parts)
    if history_text:
        contents.append(f"Chat History:\n{history_text}")
    if text:
        contents.append(f"Current User Input: {text}")

    if not contents:
        return "No content provided."

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )
    return response.text
