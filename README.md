## Telegram Chatbot with Chat GPT and DALL-E

This is a simple Telegram chatbot that listens for incoming messages and uses Chat GPT to generate replies. The bot is
built using Python and the Telegram Bot API. In addition, this bot also uses DALL-E to generate images from text input.

### Installation
1. Clone the repository to your local machine.
    ```bash
    git clone https://github.com/nikhilbadyal/tgpt-replier.git
    ```
2. Install the required Python packages.
    ```bash
    pip install -r requirements.txt
    ```
3. Add Environment Variables in .env file.

## Usage

1. Once the script is running, you can start chatting on Telegram. The script will listen for incoming messages and
   generate replies using Chat GPT.
2. If the message contains **'/image'** in the beginning, the bot will use DALL-E to generate an image based on the
   text input.
   **For example**, if you send a message like "/image Can you generate an image of a cat sleeping on a bed?",
   the bot will use DALL-E to generate an image of a cat sleeping on a bed and send it back to you on Telegram.
3. In addition to generating images, the bot can also perform other tasks based on user input. For example, it can provide information about a particular topic, answer questions, or play simple games with users.
