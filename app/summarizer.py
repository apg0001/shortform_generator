# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
# import nltk
# # from .crwaler import Crawler


# class Summarizer:
#     def __init__(self, model_dir="lcw99/t5-base-korean-text-summary"):
#         self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
#         self.model = AutoModelForSeq2SeqLM.from_pretrained(model_dir)
#         self.max_input_length = 2048

#     def summarize(self, text, max_length=128):
#         inputs = self.tokenizer([text], max_length=self.max_input_length,
#                                 truncation=True, return_tensors="pt", padding=True)
#         output = self.model.generate(
#             **inputs, num_beams=16, do_sample=False, min_length=1, max_length=max_length)
#         decoded = self.tokenizer.batch_decode(
#             output, skip_special_tokens=True)[0]
#         return nltk.sent_tokenize(decoded.strip())[0]


from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import nltk
# from crawler import Crawler


class Summarizer:
    def __init__(self, model_dir="lcw99/t5-base-korean-text-summary"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_dir)
        self.max_input_length = 2048

    def summarize(self, text, max_length=128):
        inputs = self.tokenizer([text], max_length=self.max_input_length,
                                truncation=True, return_tensors="pt", padding=True)
        output = self.model.generate(
            **inputs, num_beams=16, do_sample=False, min_length=1, max_length=max_length
        )
        decoded = self.tokenizer.batch_decode(output, skip_special_tokens=True)[0]
        # 한 문장만 쓰고 싶지 않다면 아래 라인 대신 decoded.strip() 전체 반환도 가능
        return nltk.sent_tokenize(decoded.strip())[0]

    # --- 추가: 문단 분리
    def _split_paragraphs(self, text: str):
        # 연속 개행을 모두 문단 경계로 보고, 공백 문단 제거
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        return paras

    # --- 추가: 500자 이상이 되도록 문단 묶어서 요약 → 요약문들 "\n\n"로 합치기
    def summarize_aggregated(self, text: str, min_chars: int = 500, max_length: int = 128) -> str:
        paragraphs = self._split_paragraphs(text)
        if not paragraphs:
            return ""

        chunks = []
        buf = []

        def buf_len(b):  # 현재 버퍼 글자 수
            return sum(len(x) for x in b) + max(0, (len(b) - 1) * 2)  # 문단 사이 "\n\n" 고려(optional)

        for p in paragraphs:
            buf.append(p)
            if buf_len(buf) >= min_chars:
                chunks.append("\n\n".join(buf))
                buf = []

        # 남은 문단이 있으면 마지막 chunk로
        if buf:
            # 너무 짧으면 직전 chunk와 합쳐도 됨. 여기선 그대로 둠.
            chunks.append("\n\n".join(buf))

        # 각 chunk를 개별 요약
        summaries = []
        for chunk in chunks:
            # tokenizer max_input_length 넘는 경우를 대비한 안전장치(토크나이저 내부에서 truncation도 있으나 이중 보강)
            if len(chunk) > self.max_input_length * 4:  # 대략적 문자수→토큰 변환 여유
                chunk = chunk[: self.max_input_length * 4]
            summ = self.summarize(chunk, max_length=max_length)
            summaries.append(summ.strip())

        # 결과를 문단 구분 유지 형태로 반환
        return "\n\n".join(summaries)


# if __name__ == "__main__":
#     crawler = Crawler()
#     url = "https://n.news.naver.com/article/584/0000033842?cds=news_media_pc&type=editn"
#     content = crawler.extract_article(url)
#     print(content)

#     summarizer = Summarizer()
#     summary = summarizer.summarize_aggregated(content)
#     print(summary)
