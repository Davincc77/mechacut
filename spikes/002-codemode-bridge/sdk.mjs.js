type JsonRepairInput = {
    /** the broken JSON text */
    text: string;
}
type JsonRepairOutput = unknown
type HashDigestInput = {
    data: string;
    algo?: "md5" | "sha1" | "sha256" | "sha512" | "blake2b";
    input_kind?: "text" | "base64" | "hex";
}
type HashDigestOutput = unknown
type TextCaseInput = {
    text: string;
    op?: "snake" | "kebab" | "camel" | "pascal" | "title" | "upper" | "lower" | "sentence";
}
type TextCaseOutput = unknown
type SortNaturalInput = {
    items: string[];
    reverse?: boolean;
}
type SortNaturalOutput = unknown
type ListDedupeInput = {
    /** the list to dedupe */
    items: unknown[];
    mode?: "exact" | "text" | "url" | "email";
}
type ListDedupeOutput = unknown
type NumRoundInput = {
    /** number or numeric string */
    value: unknown;
    places?: number;
    mode?: "half_even" | "half_up" | "half_down" | "ceil" | "floor" | "trunc" | "up";
    significant?: boolean;
}
type NumRoundOutput = unknown
type DateParseInput = {
    text: string;
    /** order for slashed ambiguous dates */
    prefer?: "dmy" | "mdy";
    /** IANA zone to interpret a naive value in */
    tz?: string;
}
type DateParseOutput = unknown
type IdSlugInput = {
    text: string;
    sep?: "-" | "_";
    lower?: boolean;
    /** 0 = unlimited */
    max_len?: number;
}
type IdSlugOutput = unknown

declare const codemode: {
	/**
	 * Repair broken JSON text deterministically (markdown fences, BOM, smart/single quotes, comments, bare keys, trailing comm
	 * @param input.text - the broken JSON text
	 */
	json_repair: (input: JsonRepairInput) => Promise<JsonRepairOutput>;

	/**
	 * Digests (md5/sha1/sha256/sha512/blake2b) over text, base64 or hex input. A model cannot hash and will confidently fake o
	 */
	hash_digest: (input: HashDigestInput) => Promise<HashDigestOutput>;

	/**
	 * Case conversion both directions: snake/kebab/camel/pascal/title/upper/lower/sentence, word-boundary aware (parseHTTPResp
	 */
	text_case: (input: TextCaseInput) => Promise<TextCaseOutput>;

	/**
	 * Human-order sort (file2 before file10) over strings, stable, with the exact permutation index so you can reapply it else
	 */
	sort_natural: (input: SortNaturalInput) => Promise<SortNaturalOutput>;

	/**
	 * Dedupe a list keeping the first occurrence and the original values: modes exact | text (NFC, whitespace, casefold) | url
	 * @param input.items - the list to dedupe
	 */
	list_dedupe: (input: ListDedupeInput) => Promise<ListDedupeOutput>;

	/**
	 * Exact Decimal rounding: places 0-30 or significant digits, modes half_even (banker's, default) | half_up | half_down | c
	 * @param input.value - number or numeric string
	 */
	num_round: (input: NumRoundInput) => Promise<NumRoundOutput>;

	/**
	 * Parse one date (ISO 8601, RFC 2822, epoch seconds, slashed numeric with explicit dmy/mdy preference — never guessed — or
	 * @param input.prefer - order for slashed ambiguous dates
	 * @param input.tz - IANA zone to interpret a naive value in
	 */
	date_parse: (input: DateParseInput) => Promise<DateParseOutput>;

	/**
	 * Title -> url-safe slug: NFKD transliteration, separators collapsed, optional word-boundary max_len cut. Free.
	 * @param input.max_len - 0 = unlimited
	 */
	id_slug: (input: IdSlugInput) => Promise<IdSlugOutput>;
}