В качестве инструмента работы с базой данных использовался DBeaver 26.1.0.
Результаты запроса экспортировались в md формате из DBeaver.


# Задача 1

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
