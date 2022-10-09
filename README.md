# News Aggregator
Решение задачи создания сервиса агрегации новостей от команды "Клика".

## Запуск
Перед клонированием репозитория установите [Git LFS](https://git-lfs.github.com/)! 
Для запуска необходимо установить [Anaconda](https://docs.anaconda.com/anaconda/install/index.html)

```bash
# Создание и активация виртуального окружения
conda env create -f environment.yml
conda activate news-aggregator

# Загрузка весов и распаковка
wget https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.ru.300.bin.gz
gzip -d cc.ru.300.bin.gz
mv cc.ru.300.bin add_data/
```

### Запуск веб-сервиса
```bash
python run.py
```

### Запуск бота
```bash
docker-compose up -d
python run_bot.py
```

### Запуск парсеров

Все парсеры находятся в модуле parsers. Каждый парсер запускается с помощью `python -m parsers.имя_парсера`.

### Запуск построения индексов и обучения моделей
```bash
cd папка/с/файлами/от/парсеров
PYTHONPATH=projectroot python project_root/data_collector/__main__.py
PYTHONPATH=projectroot python project_root/ml/okved_match/__main__.py
PYTHONPATH=projectroot python project_root/ml/news_lookup/__main__.py
```
