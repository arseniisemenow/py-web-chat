FROM tiangolo/uvicorn-gunicorn:python3.10

WORKDIR /py_web_chat

COPY ./app /py_web_chat/app
COPY ./requirements.txt /py_web_chat/requirements.txt

RUN pip install -r requirements.txt

COPY ./wait-for-it.py /py_web_chat/wait-for-it.py

CMD ["sh", "-c", "python wait-for-it.py db:5432 -- && uvicorn app.main:app --reload --host 0.0.0.0"]