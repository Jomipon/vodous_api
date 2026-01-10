create table public.word_content
(
  word_id text not null DEFAULT ((gen_random_uuid())::text),
  word_content text not null,
  word_language text not null,
  valid boolean not null default false,
  created_at timestamp with time zone not null default now(),
  note text null,
  tts_path text null,
  constraint word_content_pkey primary key (word_id)
) TABLESPACE pg_default;

create table public.word_translate
(
  word_translate_id text not null DEFAULT ((gen_random_uuid())::text),
  word_from_id text not null,
  word_to_id text not null,
  valid boolean not null default false,
  created_at timestamp with time zone not null default now(),
  note text null,
  success_rate float null,
  constraint word_translate_pkey primary key (word_translate_id)
) TABLESPACE pg_default;


create table public.word_translate_success_rate
(
  word_translate_score text not null DEFAULT ((gen_random_uuid())::text),
  word_translate_id text not null,
  success_rate float not null,
  created_at timestamp with time zone not null default now(),
  constraint word_translate_score_pkey primary key (word_translate_score)
) TABLESPACE pg_default;

create table public.word_tts
(
  word_id text not null,
  file_name text not null,
  duration_seconds integer,
  mime_type text,
  word_tts bytea not null,
  created_at timestamp with time zone not null default now(),
  constraint word_tts_pkey primary key (word_id)
) TABLESPACE pg_default;


create table public.word_translate_success_rate
(
  word_translate_score text not null DEFAULT ((gen_random_uuid())::text),
  word_translate_id text not null,
  success_rate float not null,
  created_at timestamp with time zone not null default now(),
  constraint word_translate_score_pkey primary key (word_translate_score)
) TABLESPACE pg_default;

CREATE OR REPLACE VIEW words_all_with_translate
as
select 
con_from.word_id as word_id_from,
con_from.word_content as word_content_from,
con_from.word_language as word_language_from,
con_from.valid as valid_from,
con_from.note as note_from,
tran.word_translate_id,
tran.word_from_id,
tran.word_to_id,
tran.valid as translate_valid,
tran.created_at as translate_created_at,
tran.note as translate_note,
tran.success_rate as translate_success_rate,
con_to.word_id as word_id_to,
con_to.word_content as word_content_to,
con_to.word_language as word_language_to,
con_to.valid as valid_to,
con_to.note as note_to,
uuid_generate_v4()::text as random_id
from word_content as con_from
left join word_translate as tran on con_from.word_id = tran.word_from_id
left join word_content con_to on tran.word_to_id = con_to.word_id
