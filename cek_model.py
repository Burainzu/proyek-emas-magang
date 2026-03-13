import google.generativeai as genai

# Masukkan API key kamu langsung di sini untuk testing
genai.configure(api_key="AIzaSyBviPE0HSBW35H2Euv-nNpODMyVBExuhk0")

print("Model yang tersedia:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)