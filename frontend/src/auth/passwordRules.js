// Misma politica que el backend (app/iam/security.py). (Responsable: Mariana)
export function passwordChecks(pw) {
  return [
    { key: "rule_length", ok: pw.length >= 8 },
    { key: "rule_letter", ok: /[A-Za-z]/.test(pw) },
    { key: "rule_number", ok: /\d/.test(pw) },
  ];
}
