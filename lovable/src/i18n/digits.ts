const FA_DIGITS = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];

export function toFaDigits(input: string | number): string {
  return String(input).replace(/[0-9]/g, (d) => FA_DIGITS[Number(d)]);
}

export function maybeFa(lang: "fa" | "en", input: string | number): string {
  return lang === "fa" ? toFaDigits(input) : String(input);
}
