create table public.word_content
(
  word_id text not null DEFAULT ((auth.uid())::text),
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
  word_translate_id text not null DEFAULT ((auth.uid())::text),
  word_cz_id text not null,
  word_en_id text not null,
  valid boolean not null default false,
  created_at timestamp with time zone not null default now(),
  note text null,
  constraint word_translate_pkey primary key (word_translate_id)
) TABLESPACE pg_default;

