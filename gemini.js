import { GoogleGenAI } from '@google/genai';

// Automatically uses process.env.GEMINI_API_KEY
const ai = new GoogleGenAI();

async function generateText(prompt) {
  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: prompt,
  });
  
  return response.text;
}

// Example usage
generateText("Hello Gemini!").then(console.log);