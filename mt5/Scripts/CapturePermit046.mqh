#ifndef FXDL_CAPTURE_PERMIT_046
#define FXDL_CAPTURE_PERMIT_046
// Pure receipt check only. No IPC, quote, file or order calls; not deployed.
// Production must obtain the receipt anew from the one-use authority each run.
bool ReceiptValid046(const bool schema_ok, const bool phase_policy_match,
   const bool date_ok, const int permission, const long issued_boot_ms,
   const long expires_boot_ms, const long expires_utc_ms,
   const long now_boot_ms, const long now_utc_ms)
{
   if(!schema_ok || !phase_policy_match || !date_ok || permission != 1) return false;
   if(issued_boot_ms < 0 || now_boot_ms < issued_boot_ms || now_boot_ms >= expires_boot_ms) return false;
   // Bound before subtraction to avoid signed overflow on malformed messages.
   if(issued_boot_ms > 9007199254740991 || expires_boot_ms > 9007199254740991 ||
      now_boot_ms > 9007199254740991 || now_utc_ms <= 0 || now_utc_ms > 32535215999999 ||
      expires_utc_ms <= 0 || expires_utc_ms > 32535215999999) return false;
   if(expires_boot_ms-issued_boot_ms > 2000 || expires_utc_ms <= now_utc_ms ||
      expires_utc_ms-now_utc_ms > 2000) return false;
   return true;
}
#endif
