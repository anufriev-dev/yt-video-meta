import csv
import re
from googleapiclient.discovery import build
from datetime import datetime

# Замените 'YOUR_API_KEY' на ваш API ключ
api_key = 'YOUR_API_KEY'
channel_id = 'ID'  # Замените на ID канала

# Создаем объект YouTube API
youtube = build('youtube', 'v3', developerKey=api_key)

# Получаем ID видео с канала
def get_video_ids(channel_id):
    video_ids = []
    request = youtube.channels().list(part='contentDetails', id=channel_id)
    response = request.execute()

    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    next_page_token = None
    while True:
        request = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            video_ids.append(item['snippet']['resourceId']['videoId'])

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return video_ids

# Преобразование ISO 8601 в HH:MM:SS
def convert_duration(iso_duration):
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
    if match:
        hours = match.group(1) or '00'
        minutes = match.group(2) or '00'
        seconds = match.group(3) or '00'
    else:
        # Установите значение по умолчанию, если формат не распознан
        return "00:00:00"  # Или любое другое значение по умолчанию

    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

# Форматирование даты с русскими днями недели и месяцами
def format_date(date_string):
    date_obj = datetime.fromisoformat(date_string[:-1])  # Удаляем "Z" в конце строки

    # Замена английских месяцев на русские
    months = {
        'jan': 'янв.',
        'feb': 'фев.',
        'mar': 'мар.',
        'apr': 'апр.',
        'may': 'май',
        'jun': 'июн.',
        'jul': 'июл.',
        'aug': 'авг.',
        'sep': 'сен.',
        'oct': 'окт.',
        'nov': 'ноя.',
        'dec': 'дек.'
    }

    # Форматируем дату
    formatted_date = date_obj.strftime(f"%d-{months[date_obj.strftime('%b').lower()]} %Y %H:%M")

    # Замена английских дней недели на русские
    weekdays = {
        'mon': 'пн',
        'tue': 'вт',
        'wed': 'ср',
        'thu': 'чт',
        'fri': 'пт',
        'sat': 'сб',
        'sun': 'вс'
    }

    weekday_abbr = date_obj.strftime("%a").lower()  # Получаем сокращенное название дня недели
    formatted_date += f" {weekdays.get(weekday_abbr, '')}"  # Добавляем русский день недели

    return formatted_date

# Получаем информацию о видео
def get_video_details(video_ids):
    video_data = []

    for i in range(0, len(video_ids), 50):  # Пакетная обработка по 50 видео
        request = youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=','.join(video_ids[i:i + 50])
        )
        response = request.execute()

        for item in response['items']:
            title = item['snippet']['title']
            views = item['statistics'].get('viewCount', 'N/A')
            likes = item['statistics'].get('likeCount', 'N/A')
            publish_date = format_date(item['snippet']['publishedAt'])  # Форматируем дату
            duration_iso = item['contentDetails']['duration']
            print(f"Duration ISO: {duration_iso}")  # Отладочная информация
            duration_formatted = convert_duration(duration_iso)
            video_url = f"https://www.youtube.com/watch?v={item['id']}"

            video_data.append({
                'title': title,
                'views': views,
                'likes': likes,
                'publish_date': publish_date,
                'url': video_url,
                'duration': duration_formatted
            })

    return video_data

# Записываем данные в CSV файл с форматом времени
def save_to_csv(video_data, filename='video_data.csv'):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['Номер', 'Название',
                                                  'Просмотры',
                                                  'Кол-Во лайков',
                                                  'Дата создания',
                                                  'Ссылка',
                                                  'Продолжительность'])
        writer.writeheader()

        for index, video in enumerate(video_data, start=1):
            writer.writerow({
                'Номер': index,
                'Название': video['title'],
                'Просмотры': video['views'],
                'Кол-Во лайков': video['likes'],
                'Дата создания': video['publish_date'],  # Записываем отформатированную дату
                'Ссылка': video['url'],
                'Продолжительность': video['duration']  # Записываем в формате HH:MM:SS
            })

# Основная функция
def main():
    video_ids = get_video_ids(channel_id)
    video_data = get_video_details(video_ids)
    save_to_csv(video_data)

if __name__ == '__main__':
    main()
