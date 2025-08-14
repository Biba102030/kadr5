import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
from utils.storage import load_cache, save_cache

async def fetch_articles_from_site(query=None, lang="ru", limit=10):
    """Получение списка статей с сайта Kadrovik.uz"""
    start_time = time.time()
    base_url = "https://kadrovik.uz/" if lang == "ru" else "https://kadrovik.uz/uz/"
    url = base_url if not query else f"{base_url}search?q={query}"
    print(f"{datetime.now()}: Начало парсинга URL: {url}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as response:
                response.raise_for_status()
                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")

        articles = []
        
        if query:
            # Для поиска используем старые селекторы
            results_list = soup.select("ol.results li")
            if results_list:
                print(f"{datetime.now()}: Найдена страница поиска со старой структурой")
                for li in results_list[:limit]:
                    a_tag = li.find('a')
                    span_date = li.find('span', class_='date')

                    url_link = a_tag['href'] if a_tag else ''
                    title = a_tag.get_text(strip=True) if a_tag else ''
                    date = span_date.get_text(strip=True) if span_date else ''
                          
                    if a_tag:
                        a_tag.extract()
                    if span_date:
                        span_date.extract()

                    text_content = li.get_text(separator=' ', strip=True)

                    if not url_link.startswith("http"):
                        url_link = base_url.rstrip("/") + "/" + url_link.lstrip("/")

                    articles.append({
                        "title": title or "Без заголовка",
                        "content": text_content or "",
                        "date": date or datetime.now().isoformat(),
                        "emoji": "📰",
                        "url": url_link
                    })
        else:
            # Для главной страницы парсим <ul class="posts-list">
            print(f"{datetime.now()}: Парсим главную страницу, ищем <ul class='posts-list'>")
            posts_list = soup.select("ul.posts-list li.post-card-wrapper, ul.posts-list li.post-card--horizontal-wrapper")
            if posts_list:
                print(f"{datetime.now()}: Найдено {len(posts_list)} статей в <ul class='posts-list'>")
                for item in posts_list[:limit]:
                    a_tag = item.find('a', href=True)
                    title_tag = item.find('h4', class_='post-card__title')
                    date_tag = item.find('time', class_='longread-post__time-published')

                    url_link = a_tag['href'] if a_tag else ''
                    title = title_tag.get_text(strip=True) if title_tag else 'Без заголовка'
                    date = date_tag.get_text(strip=True) if date_tag else datetime.now().strftime('%d.%m.%Y')

                    if not url_link.startswith("http"):
                        url_link = base_url.rstrip("/") + "/" + url_link.lstrip("/")

                    articles.append({
                        "title": title,
                        "content": "",  # Краткое описание не извлекаем, так как его нет в HTML
                        "date": date,
                        "emoji": "📰",
                        "url": url_link
                    })
            
            # Резервная логика для новой структуры сайта
            if not articles:
                print(f"{datetime.now()}: Ищем статьи в новой структуре сайта")
                article_links = []
                potential_selectors = [
                    "a[href*='/publish/']",
                    "a[href*='/article/']",
                    ".article-link",
                    ".publication-link",
                    "article a",
                    ".content a[href]",
                    "main a[href]"
                ]
                
                for selector in potential_selectors:
                    links = soup.select(selector)
                    if links:
                        print(f"{datetime.now()}: Найдены ссылки с селектором: {selector} ({len(links)} штук)")
                        article_links.extend(links)
                        break
                
                if not article_links:
                    all_links = soup.find_all('a', href=True)
                    article_links = [
                        link for link in all_links 
                        if any(keyword in link['href'] for keyword in ['/publish/', '/article/', '/news/'])
                        and not any(skip in link['href'] for skip in ['search', 'group', 'recent_publications'])
                    ]
                    print(f"{datetime.now()}: Найдены общие ссылки на статьи: {len(article_links)}")
                
                processed_urls = set()
                for link in article_links[:limit*2]:
                    if len(articles) >= limit:
                        break
                        
                    href = link.get('href', '')
                    if not href or href in processed_urls:
                        continue
                        
                    if not href.startswith("http"):
                        href = base_url.rstrip("/") + "/" + href.lstrip("/")
                    
                    processed_urls.add(href)
                    
                    title = link.get_text(strip=True)
                    if not title:
                        continue
                    
                    date = ""
                    parent = link.parent
                    if parent:
                        date_elem = parent.find('time') or parent.find(class_='date') or parent.find('span', string=lambda text: text and any(month in text for month in ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня']))
                        if date_elem:
                            date = date_elem.get_text(strip=True)
                    
                    content = ""
                    if parent:
                        text_nodes = parent.find_all(text=True)
                        content_parts = []
                        for text_node in text_nodes:
                            text = text_node.strip()
                            if text and text != title and len(text) > 10:
                                content_parts.append(text)
                        content = ' '.join(content_parts[:2])
                    
                    articles.append({
                        "title": title,
                        "content": content[:200] + "..." if len(content) > 200 else content,
                        "date": date or datetime.now().isoformat(),
                        "emoji": "📰",
                        "url": href
                    })

        print(f"{datetime.now()}: Найдено статей перед срезом: {len(articles)}")
        articles = articles[:limit]
        print(f"{datetime.now()}: Возвращено статей после среза: {len(articles)}")
        
        if not articles:
            print(f"{datetime.now()}: Не удалось найти статьи по URL: {url}")
            all_links = soup.find_all('a', href=True)[:5]
            for i, link in enumerate(all_links):
                print(f"{datetime.now()}: {i+1}. {link.get('href')} - {link.get_text(strip=True)[:50]}")
        
        print(f"{datetime.now()}: Парсинг завершен. Время: {time.time() - start_time:.2f} сек. Найдено статей: {len(articles)}")
        
        cache = load_cache()
        cache_key = f"latest_{lang}" if not query else f"search_{query}_{lang}"
        cache[cache_key] = {
            "timestamp": datetime.now().isoformat(),
            "data": articles
        }
        save_cache(cache)
        return articles
    except Exception as e:
        print(f"{datetime.now()}: Ошибка при парсинге сайта: {e}. Время: {time.time() - start_time:.2f} сек")
        cache = load_cache()
        cache_key = f"latest_{lang}" if not query else f"search_{query}_{lang}"
        return cache.get(cache_key, {}).get("data", [])

async def fetch_article_content(url):
    """Парсер с правильными переносами строк после emoji и абзацев"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                response.raise_for_status()
                html = await response.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Без заголовка"
        date_elem = soup.find('time', {'class': 'longread-post__time-published'})
        date = date_elem['datetime'] if date_elem else ""
        
        content_block = soup.find('section', {'class': 'longread-block'}) or soup.find('body')
        
        if not content_block:
            return f"📰 {title}\n📅 {date}\n\nНе удалось найти контент."
        
        elements = content_block.find_all(['p', 'strong'])
        result = []
        
        for element in elements:
            text = element.get_text(' ', strip=True)
            if text:
                if element.name == 'strong':
                    result.append(f"\n \n🔹 {text}\n")
                else:
                    result.append(f"{text}")
        
        content = ''.join(dict.fromkeys(result))
        
        return content if len(content) > 50 else "Не удалось извлечь текст."
    
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

async def search_articles(query, lang):
    """Поиск статей по запросу"""
    cache = load_cache()
    cache_key = f"search_{query}_{lang}"
    
    if cache_key in cache:
        entry = cache[cache_key]
        timestamp = entry.get("timestamp")
        if timestamp and (datetime.now() - datetime.fromisoformat(timestamp)) < timedelta(hours=24):
            print(f"{datetime.now()}: Используем кэшированные данные для запроса: {query}")
            return entry["data"]

    print(f"{datetime.now()}: Парсинг сайта для запроса: {query}")
    articles = await fetch_articles_from_site(query, lang)
    return articles

async def get_latest_articles(lang):
    """Получение последних статей"""
    cache = load_cache()
    cache_key = f"latest_{lang}"
    
    if cache_key in cache:
        entry = cache[cache_key]
        timestamp = entry.get("timestamp")
        if timestamp and (datetime.now() - datetime.fromisoformat(timestamp)) < timedelta(hours=24):
            print(f"{datetime.now()}: Используем кэшированные данные для последних статей ({lang})")
            return entry["data"]

    print(f"{datetime.now()}: Парсинг сайта для последних статей ({lang})")
    articles = await fetch_articles_from_site(lang=lang, limit=5)  # Лимит 5 для актуальных статей
    return articles