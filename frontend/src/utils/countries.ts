const countryCodeMap: Record<string, string> = {
  IN: 'India',
  NP: 'Nepal',
  CN: 'China',
  HK: 'Hong Kong',
  BD: 'Bangladesh',
  PK: 'Pakistan',
  TH: 'Thailand',
  VN: 'Vietnam',
  SG: 'Singapore',
  MY: 'Malaysia',
  IQ: 'Iraq',
  AE: 'UAE',
  ET: 'Ethiopia',
  KE: 'Kenya',
  RW: 'Rwanda',
  US: 'United States',
}

export function getCountryName(code: string): string {
  return countryCodeMap[code] || code
}
