INITIAL_RESPONSE = "正在运算中......"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"


def create_prompt(transcript):
        return f"""假如你是一个程序员，参加一场面试。
        {transcript}请用中文回答我
        """

""" 你的 APPID AK SK """
APP_ID = 'YOUR_APP_ID'
API_KEY = 'YOUR_API_KEY'
SECRET_KEY = 'YOUR_SECRET_KEY'