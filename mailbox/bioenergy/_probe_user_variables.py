"""Enumerate ALL 90 LEAP User Variables. Find RenewableCapacityTarget
and ASEANRenewableCapacityTarget — get their host branch + definition."""
from pathlib import Path
from nemo_read._leap_com import dispatch_leap, safe_expression


OUT = Path(__file__).parent / "_user_variables_findings.txt"


def log(msg: str = "") -> None:
    print(msg, flush=True)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def main() -> None:
    OUT.write_text("", encoding="utf-8")
    leap = dispatch_leap()
    log(f"=== ENV ===")
    log(f"Area: {leap.ActiveArea.Name!r}")
    log(f"Scenario: {leap.ActiveScenario.Name!r}")
    log("")

    uvars = leap.UserVariables
    cnt = uvars.Count
    log(f"=== {cnt} User Variables ===")

    # First pass: list all names
    interesting = []
    for i in range(1, cnt + 1):
        try:
            uv = uvars.Item(i)
        except Exception as e:
            log(f"  #{i}  ERR getting item: {e}")
            continue

        # Try various property names — LEAP COM property names can vary
        details = {"#": i}
        for prop in ("Name", "Caption", "FullName", "Description"):
            try:
                v = getattr(uv, prop)
                details[prop] = v
            except Exception:
                pass
        # Branch property
        try:
            br = uv.Branch
            details["Branch"] = br.FullName
            details["BranchID"] = br.ID
        except Exception:
            try:
                details["Branch"] = uv.BranchName
            except Exception:
                pass

        log(f"  #{i}: {details}")

        # Mark interesting
        name = details.get("Name") or details.get("Caption") or ""
        if any(kw in name for kw in (
            "Renewable", "RECapacity", "RE Capacity", "ASEAN", "Capacity Target",
        )):
            interesting.append((i, details, uv))

    log("")
    log(f"=== Interesting ones ({len(interesting)}) ===")
    for i, details, uv in interesting:
        log(f"\n  #{i}: {details}")
        # Try to read its expression / value
        for prop in ("Expression", "Value", "Definition", "Formula"):
            try:
                v = getattr(uv, prop)
                log(f"    {prop} = {v!r}")
            except Exception as e:
                log(f"    {prop} ERR: {e}")

    log("")
    log("=== DONE ===")


if __name__ == "__main__":
    main()
