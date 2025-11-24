/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import { GoogleGenAI } from "@google/genai";
import { CampaignDraft } from "../types";

const getAi = () => {
  return new GoogleGenAI({ apiKey: process.env.API_KEY });
};

const TEXT_MODEL = 'gemini-2.5-flash';

export const generateCampaignProposal = async (
  topic: string,
  sentimentContext: string,
  platform: string
): Promise<CampaignDraft> => {
  
  const prompt = `
    You are a senior crisis management and marketing strategist.
    A user wants to start a new campaign to address a specific topic found in social listening.

    Topic: "${topic}"
    Context/Sentiment: The general sentiment is ${sentimentContext}.
    Primary Platform source: ${platform}

    Please generate a structured campaign proposal that includes:
    1. A strategic approach (how to handle this sentiment).
    2. Draft content for a post or response (keep it professional but empathetic).
    3. Recommended channels to distribute this message.

    Return the response in strictly valid JSON format with the following schema:
    {
      "strategy": "string",
      "content": "string",
      "channels": ["string", "string"]
    }
  `;

  try {
    const response = await getAi().models.generateContent({
      model: TEXT_MODEL,
      contents: prompt,
      config: {
        responseMimeType: "application/json",
      }
    });

    const text = response.text;
    if (!text) throw new Error("No response from AI");

    const json = JSON.parse(text);

    return {
      topic: topic,
      strategy: json.strategy || "Engage directly with users to resolve concerns.",
      content: json.content || "We hear you and we are working on it.",
      channels: json.channels || ["LinkedIn", "Twitter"]
    };

  } catch (error) {
    console.error("AI Generation Error:", error);
    // Fallback if JSON parsing fails or API errors
    return {
      topic,
      strategy: "Direct Engagement Strategy (Fallback due to connection error)",
      content: "We appreciate your feedback regarding " + topic + " and are actively investigating. Please reach out to support.",
      channels: ["Official Support Channels"]
    };
  }
};
