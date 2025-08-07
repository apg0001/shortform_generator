from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import nltk
from crwaler import Crawler


class Summarizer:
    def __init__(self, model_dir="lcw99/t5-base-korean-text-summary"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_dir)
        self.max_input_length = 2048

    def summarize(self, text, max_length=128):
        inputs = self.tokenizer([text], max_length=self.max_input_length,
                                truncation=True, return_tensors="pt", padding=True)
        output = self.model.generate(
            **inputs, num_beams=16, do_sample=False, min_length=1, max_length=max_length)
        decoded = self.tokenizer.batch_decode(
            output, skip_special_tokens=True)[0]
        return nltk.sent_tokenize(decoded.strip())[0]


if __name__ == "__main__":
    crawler = Crawler()
    url = "https://n.news.naver.com/article/009/0005537920?cds=news_media_pc&type=editn"
    content = crawler.extract_article(url)

    summarizer = Summarizer()
    summary = summarizer.summarize(content)
    print(summary)
