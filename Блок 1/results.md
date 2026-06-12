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
|genre|region|total_listens|
|-----|------|-------------|
|Alternative|Kazan|149|
|Electronic|Kazan|114|
|Funk|Kazan|130|
|Hip-Hop|Kazan|221|
|Indie|Kazan|125|
|Jazz|Kazan|212|
|Pop|Kazan|132|
|R&B|Kazan|123|
|Rock|Kazan|198|
|Soul|Kazan|130|
|Alternative|Krasnoyarsk|147|
|Electronic|Krasnoyarsk|124|
|Funk|Krasnoyarsk|131|
|Hip-Hop|Krasnoyarsk|215|
|Indie|Krasnoyarsk|107|
|Jazz|Krasnoyarsk|190|
|Pop|Krasnoyarsk|146|
|R&B|Krasnoyarsk|142|
|Rock|Krasnoyarsk|244|
|Soul|Krasnoyarsk|144|
|Alternative|Moscow|125|
|Electronic|Moscow|114|
|Funk|Moscow|122|
|Hip-Hop|Moscow|200|
|Indie|Moscow|131|
|Jazz|Moscow|187|
|Pop|Moscow|139|
|R&B|Moscow|124|
|Rock|Moscow|236|
|Soul|Moscow|126|
|Alternative|Nizhny Novgorod|147|
|Electronic|Nizhny Novgorod|119|
|Funk|Nizhny Novgorod|134|
|Hip-Hop|Nizhny Novgorod|223|
|Indie|Nizhny Novgorod|117|
|Jazz|Nizhny Novgorod|219|
|Pop|Nizhny Novgorod|167|
|R&B|Nizhny Novgorod|143|
|Rock|Nizhny Novgorod|207|
|Soul|Nizhny Novgorod|134|
|Alternative|Novosibirsk|139|
|Electronic|Novosibirsk|112|
|Funk|Novosibirsk|122|
|Hip-Hop|Novosibirsk|231|
|Indie|Novosibirsk|125|
|Jazz|Novosibirsk|214|
|Pop|Novosibirsk|131|
|R&B|Novosibirsk|109|
|Rock|Novosibirsk|215|
|Soul|Novosibirsk|137|
|Alternative|Saint Petersburg|148|
|Electronic|Saint Petersburg|106|
|Funk|Saint Petersburg|121|
|Hip-Hop|Saint Petersburg|203|
|Indie|Saint Petersburg|104|
|Jazz|Saint Petersburg|190|
|Pop|Saint Petersburg|138|
|R&B|Saint Petersburg|117|
|Rock|Saint Petersburg|209|
|Soul|Saint Petersburg|126|
|Alternative|Samara|122|
|Electronic|Samara|121|
|Funk|Samara|100|
|Hip-Hop|Samara|200|
|Indie|Samara|104|
|Jazz|Samara|205|
|Pop|Samara|143|
|R&B|Samara|140|
|Rock|Samara|208|
|Soul|Samara|146|
|Alternative|Sochi|122|
|Electronic|Sochi|108|
|Funk|Sochi|115|
|Hip-Hop|Sochi|231|
|Indie|Sochi|131|
|Jazz|Sochi|185|
|Pop|Sochi|154|
|R&B|Sochi|129|
|Rock|Sochi|236|
|Soul|Sochi|137|
|Alternative|Vladivostok|122|
|Electronic|Vladivostok|93|
|Funk|Vladivostok|105|
|Hip-Hop|Vladivostok|195|
|Indie|Vladivostok|107|
|Jazz|Vladivostok|181|
|Pop|Vladivostok|128|
|R&B|Vladivostok|122|
|Rock|Vladivostok|202|
|Soul|Vladivostok|129|
|Alternative|Yekaterinburg|133|
|Electronic|Yekaterinburg|125|
|Funk|Yekaterinburg|119|
|Hip-Hop|Yekaterinburg|240|
|Indie|Yekaterinburg|118|
|Jazz|Yekaterinburg|211|
|Pop|Yekaterinburg|143|
|R&B|Yekaterinburg|127|
|Rock|Yekaterinburg|201|
|Soul|Yekaterinburg|133|