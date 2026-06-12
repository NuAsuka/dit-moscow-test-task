В качестве инструмента работы с базой данных использовался DBeaver 26.1.0. Результаты запроса экспортировались в md формате из DBeaver.


# Задача 1
Найди альбом, в котором суммарное количество прослушиваний песен в жанре Rock самое большое.Формат вывода: album (TEXT), artist (TEXT), listens (INTEGER)
```sql
select a.title as album, a2.name, count(ll.listen_time ) as listens
from listening_logs ll
left join songs s on s.song_id = ll.song_id
left join albums a on a.album_id = s.album_id 
left join song_genres sg on sg.song_id = s.song_id 
left join genres g on g.genre_id = sg.genre_id 
left join artists a2 on a2.artist_id = a.artist_id 
where g.name = 'Rock'
group by a.title, a2.name
order by listens desc
limit 1
```
Результат запроса:
|album|name|listens|
|-----|----|-------|
|Night Visions|Imagine Dragons|345|

# Задача 2
Определи исполнителя, у которого больше всего песен в топ-20% по количеству прослушиваний.Формат вывода: artist (TEXT), top_songs (INTEGER)
```sql
with top20 as (
select t2.song_id
from (
    SELECT *, PERCENT_RANK() OVER (ORDER BY t1.songs DESC) as pr
    FROM (select song_id, count(ll.listen_time) as songs from listening_logs ll group by song_id) t1
) t2
where t2.pr <= 0.2
)


select a.name as artist, count(distinct ll.song_id) as top_songs
from listening_logs ll 
left join songs s on s.song_id  = ll.song_id 
left join song_artists sa on sa.song_id = s.song_id
left join artists a on a.artist_id = sa.artist_id
where ll.song_id in (select song_id from top20)
group by a.name 
order by top_songs desc
limit 1
```
|artist|top_songs|
|----|---------|
|Depeche Mode|5|
# Задача 3
Найди альбом, в котором больше всего песен с несколькими артистами. В ответе покажи название альбома, основного исполнителя и количество совместных песен.Формат вывода: album (TEXT), artist (TEXT), collab_count (INTEGER)

```sql
with collab_songs as (
select sa.song_id, count(distinct sa.artist_id) as count
from song_artists sa
group by sa.song_id
having count > 1
)

select a.title as album, a2.name as artist, count(distinct s.song_id) as collab_count
from collab_songs cs
join songs s on s.song_id = cs.song_id
join albums a on s.album_id = a.album_id
join artists a2 on a2.artist_id  = a.artist_id 
group by album, artist
order by collab_count desc
limit 1
```
|album|artist|collab_count|
|-----|------|------------|
|Lemonade|Beyoncé|4|
# Задача 4
Составь таблицу с суммарным количеством прослушиваний по месяцам для всех песен.Формат вывода: year_month (TEXT, формат YYYY-MM), total_listen_count (INTEGER)
```sql
select strftime('%Y-%m', ll.listen_time) as year_month, count(ll.song_id) as total_listens
from listening_logs ll 
group by strftime('%Y-%m', ll.listen_time)
```
|year_month|total_listens|
|----------|-------------|
|2022-01|238|
|2022-02|214|
|2022-03|236|
|2022-04|231|
|2022-05|254|
|2022-06|226|
|2022-07|245|
|2022-08|252|
|2022-09|255|
|2022-10|269|
|2022-11|215|
|2022-12|247|
|2023-01|252|
|2023-02|219|
|2023-03|227|
|2023-04|250|
|2023-05|231|
|2023-06|233|
|2023-07|240|
|2023-08|270|
|2023-09|256|
|2023-10|269|
|2023-11|249|
|2023-12|253|
|2024-01|7|
# Задача 5
Составь сводную таблицу с суммарным количеством прослушиваний по жанрам и регионам.Формат вывода: genre (TEXT), region (TEXT), total_listens (INTEGER)
```sql
select g.name as genre, ll.region as region, count(*) as total_listens
from listening_logs ll 
inner join songs s using(song_id)
inner join song_genres sg using(song_id)
inner join genres g using(genre_id)
group by ll.region, g.name 
```
