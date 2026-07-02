import axios from 'axios';
import { MessageInterface } from '@/types/types';
import { API_KEY, API_URL } from '@/config/runpodConfigs';

const REQUEST_TIMEOUT_MS = 30000; // abort a hung request instead of waiting forever
const MAX_RETRIES = 2;            // retry transient (timeout / network / 5xx) failures
const HISTORY_WINDOW = 6;         // only send the most recent turns to keep payload + latency down

function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function callChatBotAPI(messages: MessageInterface[]): Promise<MessageInterface> {
    // The backend routes on recent context, so we don't need to resend the full history.
    const recentMessages = messages.slice(-HISTORY_WINDOW);

    let lastError: any;
    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
        try {
            const response = await axios.post(
                API_URL,
                { input: { messages: recentMessages } },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${API_KEY}`,
                    },
                    timeout: REQUEST_TIMEOUT_MS,
                }
            );

            const outputMessage: MessageInterface = response.data?.['output'];
            if (!outputMessage) {
                throw new Error('Malformed response from chatbot API');
            }
            return outputMessage;
        } catch (error: any) {
            lastError = error;
            // Only retry transient failures — never retry a 4xx client error.
            const status = error?.response?.status;
            const retryable = status === undefined || status >= 500;
            if (attempt < MAX_RETRIES && retryable) {
                await sleep(500 * Math.pow(2, attempt)); // 500ms, then 1s
                continue;
            }
            break;
        }
    }

    console.error('Error calling the API:', lastError);
    throw lastError;
}

export { callChatBotAPI };