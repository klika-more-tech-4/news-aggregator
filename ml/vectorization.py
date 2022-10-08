from numpy import vstack, ndarray
from torch import sum, clamp, Tensor, device, cuda, no_grad
from torch.nn.functional import normalize
from transformers import AutoTokenizer, AutoModel

from .dataset import VectorizerDataset

from typing import List


class BertVectorizer:

    def __init__(self, model_name: str, max_len: int = 512):
        self.model = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.device = device("cuda" if cuda.is_available() else "cpu")
        self.max_len = max_len

        self.model.to(self.device)

    def vectorize(self, text: List[str], batch_size: int = 2, use_pooling: bool = False) -> ndarray:
        assert len(text) > 0, "Передан пустой массив строк"

        text_dataset = VectorizerDataset(text, self.tokenizer, batch_size=batch_size)

        result = []
        for data in text_dataset:
            with no_grad():
                model_output = self.model(**{k: v.to(self.device) for k, v in data.items()})

            if use_pooling:
                embeddings = self.mean_pooling(model_output, data['attention_mask'])
            else:
                embeddings = model_output.last_hidden_state[:, 0, :]
                embeddings = normalize(embeddings)

            result.append(embeddings.cpu().numpy())

        return vstack(result)

    @staticmethod
    def mean_pooling(model_output, attention_mask: Tensor) -> Tensor:
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask
