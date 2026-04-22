#!/usr/bin/env python3
# addcustomai-consent-bypass.py
#
# Root cause of #2 ("click Add Custom Translation Service -> flash exit, no modal"):
#   b = async () => {
#     let { userValue: T, localValue: w } = await er("hasAgreedCustomServiceConsent");
#     T || w ? y() : (c(!0), ge({ key: "show_3rd_party_privacy_confirmation" }))
#   };
# The `await er("hasAgreedCustomServiceConsent")` reaches out to the remote
# user-config store via a WebSocket whose host is blocked by our DNR kill-
# switch. The call rejects, `await` throws, destructuring blows up, and the
# whole b() handler dies silently before ever calling y() -- which is the
# function that sets showModal=true. No modal appears = "flash exit".
#
# Turn 25's `x=!0` patch (inside y()) never runs because control never
# reaches y().
#
# Fix: replace the consent-gated entry with a direct call to y(), wrapped in
# try/catch for safety. This is byte-for-byte unique in options.js.
#
# Usage: python3 patches/addcustomai-consent-bypass.py [--apply]

import sys
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["options.js"]

OLD = b'b=async()=>{let{userValue:T,localValue:w}=await er("hasAgreedCustomServiceConsent");T||w?y():(c(!0),ge({key:"show_3rd_party_privacy_confirmation"}))}'
NEW = b'b=async()=>{try{y()}catch(_){}}'


def main():
    apply = "--apply" in sys.argv
    for name in FILES:
        path = os.path.join(ROOT, name)
        with open(path, "rb") as fh:
            data = fh.read()
        count = data.count(OLD)
        if count != 1:
            print(f"[{name}] SKIP: expected 1 unique match, got {count}")
            continue
        new_data = data.replace(OLD, NEW, 1)
        delta = len(new_data) - len(data)
        print(f"[{name}] match ok; delta = {delta:+d} B; {len(data)} -> {len(new_data)}")
        if apply:
            bak = path + ".bak-consent-bypass"
            if not os.path.exists(bak):
                shutil.copy2(path, bak)
                print(f"  backup -> {bak}")
            with open(path, "wb") as fh:
                fh.write(new_data)
            print(f"  wrote {path}")


if __name__ == "__main__":
    main()
