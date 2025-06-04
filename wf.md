Facebook Integration:
The application uses FastAPI to handle Facebook Messenger webhooks
Two main endpoints: verification endpoint and message handling endpoint
Verifies incoming webhooks using FB_VERIFY_TOKEN
Message Processing:
MessengerService handles all messenger-related operations
Checks for duplicate messages to avoid processing the same message twice
Manages both user messages and page admin messages
User & Thread Management:
Creates/retrieves user profiles from Facebook data
Maintains chat threads for each user
Stores messages with their types (user, bot, or page_admin)
Chat Flow:
When a user message is received:
Creates a message record in the database
Retrieves chat history
Generates response using OpenAI
Creates and stores bot response
Sends response back to Facebook Messenger
Database Integration:
Stores users, threads, and messages
Maintains message history for context
Tracks Facebook-specific IDs and message IDs
OpenAI Integration:
Uses chat history to maintain context
Generates responses using OpenAI's chat completion API
Formats messages according to OpenAI's expected format