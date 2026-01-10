CREATE OR REPLACE FUNCTION public.translate_rating_recalculation(
    p_word_translate_id text
)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE word_translate
    SET success_rate = (
        SELECT AVG(success_rate)
        FROM word_translate_success_rate
        WHERE word_translate_id = p_word_translate_id
    )
    WHERE word_translate_id = p_word_translate_id;

    RETURN;
END;
$$;
