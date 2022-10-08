class VectorizerDataset:

    def __init__(self, texts, tokenizer, batch_size=2, max_len=512):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.batch_size = batch_size
        self.idx = 0

    def __len__(self):
        return len(self.texts)

    def __iter__(self):
        return self

    def __next__(self):
        if self.idx < len(self):
            encoding_text = self.get_encoding_text(self.idx, self.idx + self.batch_size)
            self.idx += self.batch_size
            return encoding_text
        else:
            self.idx = 0
            raise StopIteration

    def get_encoding_text(self, start_idx, stop_idx):
        text = self.texts[start_idx: stop_idx]

        encoding_text = self.tokenizer(text,
                                       padding=True,
                                       truncation=True,
                                       max_length=self.max_len,
                                       return_tensors='pt')

        return encoding_text
