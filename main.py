from dotenv import load_dotenv
from PixelTunes64 import PixelTunes64

load_dotenv()

def main():
    app = PixelTunes64()
    app.run()

if __name__ == '__main__':
    main()

