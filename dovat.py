import json
import os

# Nacitanie zakonov z JSON suboru
with open("zakony.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Zlucenie vsetkych zakonov do jedneho zoznamu
all_laws = []
for category, laws in data.items():
    for law in laws:
        law["category"] = category
        all_laws.append(law)


def search_laws(query):
    q = query.lower()
    results = []
    for law in all_laws:
        if (q in law["id"].lower() or
            q in law["name"].lower() or
            q in law.get("en_name", "").lower()):
            results.append(law)
    return results


def print_selected_table(selected):
    print("\n" + "="*80)
    print(f"{'#':<4} {'ID':<20} {'Nazov':<35} {'Jail min':<10} {'Jail max':<10} {'Fine max'}")
    print("-"*80)
    for i, law in enumerate(selected, 1):
        print(f"{i:<4} {law['id']:<20} {law['name']:<35} {law.get('jail_min',0):<10} {law.get('jail_max',0):<10} ${law.get('fine_max',0)}")
    print("="*80)


def calculate_totals(selected):
    total_jail = sum(law.get("jail_max", 0) for law in selected)
    total_fine = sum(law.get("fine_max", 0) for law in selected)
    if any(law.get("jail_max", 0) == 999 for law in selected):
        total_jail = 999
    return total_jail, total_fine


def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=== DOHODA O VINE A TRESTU ===\n")

    name_p = input("Zadejte jméno pachatele: ").strip()
    dob = input("Zadejte datum narození pachatele (DD/MM/YYYY): ").strip()
    signature = input("Zadejte podpis příslušníka: ").strip()
    jail_signature = name_p.split()[-1] if name_p else ""

    selected = []

    print("\n--- Vyhladavanie trestov ---")
    print("Prikazy: [text] Enter = vyhladat | 'del' = mazat | 'koniec' = dokoncit\n")

    while True:
        if selected:
            print_selected_table(selected)
            total_jail, total_fine = calculate_totals(selected)
            print(f"  >> Celkovy trest: {total_jail} mes. | Celkova pokuta: ${total_fine}\n")

        query = input("Hladaj (alebo 'del' / 'koniec'): ").strip()

        if query.lower() == "koniec":
            if not selected:
                print("Nebol vybrany ziadny trest!")
                continue
            break

        if query.lower() == "del":
            if not selected:
                print("Zoznam je prazdny.\n")
                continue
            print_selected_table(selected)
            try:
                choice = input("Zadaj cislo trestu na vymazanie (alebo Enter pre zrusenie): ").strip()
                if choice == "":
                    continue
                idx = int(choice) - 1
                if 0 <= idx < len(selected):
                    removed = selected.pop(idx)
                    print(f"  Vymazany: {removed['id']} - {removed['name']}\n")
                else:
                    print("  Neplatne cislo.\n")
            except ValueError:
                print("  Neplatny vstup.\n")
            continue

        if not query:
            continue

        results = search_laws(query)

        if not results:
            print("  Ziadne vysledky.\n")
            continue

        if len(results) == 1:
            law = results[0]
            selected.append(law)
            print(f"  Pridany: {law['id']} - {law['name']}\n")
        else:
            print(f"\n  Najdene {len(results)} vysledkov:")
            print(f"  {'#':<4} {'ID':<20} {'Nazov':<35} {'Jail max':<10} {'Fine max'}")
            print("  " + "-"*75)
            for i, law in enumerate(results, 1):
                print(f"  {i:<4} {law['id']:<20} {law['name']:<35} {law.get('jail_max',0):<10} ${law.get('fine_max',0)}")
            print()
            try:
                choice = input("  Zadaj cislo trestu (alebo Enter pre zrusenie): ").strip()
                if choice == "":
                    continue
                idx = int(choice) - 1
                if 0 <= idx < len(results):
                    law = results[idx]
                    selected.append(law)
                    print(f"  Pridany: {law['id']} - {law['name']}\n")
                else:
                    print("  Neplatne cislo.\n")
            except ValueError:
                print("  Neplatny vstup.\n")

    # ── Faza upravy trestu ──────────────────────────────────────────────────────
    base_jail, base_fine = calculate_totals(selected)
    lwop = base_jail == 999

    jail_min = sum(l.get("jail_min", 0) for l in selected)
    jail_max = base_jail
    jail_mid = round((jail_min + jail_max) / 2) if not lwop else 999

    fine_min = sum(l.get("fine_min", 0) for l in selected)
    fine_max = base_fine
    fine_mid = round((fine_min + fine_max) / 2)

    final_jail = jail_mid
    final_fine = fine_mid

    print("\n" + "="*80)
    print("  UPRAVA TRESTU")
    print("="*80)

    def print_status(fj, ff):
        jail_label = "LWOP" if lwop else f"{fj} mes."
        print(f"\n  Jail:  min={jail_min}  stred={jail_mid}  max={jail_max}   [ AKTUALNY: {jail_label} ]")
        print(f"  Fine:  min=${fine_min}  stred=${fine_mid}  max=${fine_max}   [ AKTUALNY: ${ff} ]")
        print()
        if not lwop:
            print("  Jail  : +XX%  -XX%  =XX          (napr: +50%  -25%  =36)")
        print("  Fine  : ++XXXXX  --XXXXX  ==XXXXX   (napr: ++10000  --50000  ==22000)")
        print("  reset = stred  |  hotovo = potvrdit\n")

    print_status(final_jail, final_fine)

    while True:
        cmd = input("  Uprava: ").strip()

        if cmd.lower() == "hotovo":
            break

        if cmd.lower() == "reset":
            final_jail = jail_mid
            final_fine = fine_mid
            print("  Reset na stredne hodnoty.\n")
            print_status(final_jail, final_fine)
            continue

        # Fine priama hodnota: ==XXXXX  (pred ++ kontrolou!)
        if cmd.startswith('=='):
            try:
                val = int(cmd[2:])
                if fine_min <= val <= fine_max:
                    final_fine = val
                    print(f"  Fine nastavena priamo na ${final_fine}\n")
                else:
                    print(f"  Mimo rozsah! Povolene: ${fine_min} – ${fine_max}\n")
                print_status(final_jail, final_fine)
            except ValueError:
                print("  Neplatna hodnota.\n")
            continue

        # Fine relativne: ++XXXXX alebo --XXXXX
        if len(cmd) >= 3 and cmd[:2] in ('++', '--'):
            try:
                amount = int(cmd[2:])
                sign = 1 if cmd[:2] == '++' else -1
                final_fine = max(fine_min, min(fine_max, final_fine + sign * amount))
                print(f"  Fine nastavena na ${final_fine}\n")
                print_status(final_jail, final_fine)
            except ValueError:
                print("  Neplatna hodnota.\n")
            continue

        # Jail priama hodnota: =XX  (pred +/- kontrolou!)
        if not lwop and cmd.startswith('='):
            try:
                val = int(cmd[1:])
                if jail_min <= val <= jail_max:
                    final_jail = val
                    print(f"  Jail nastaveny priamo na {final_jail} mesiacov\n")
                else:
                    print(f"  Mimo rozsah! Povolene: {jail_min} – {jail_max} mes.\n")
                print_status(final_jail, final_fine)
            except ValueError:
                print("  Neplatna hodnota.\n")
            continue

        # Jail percenta: +XX% alebo -XX%
        if not lwop and len(cmd) >= 3 and cmd[0] in ('+', '-') and cmd[-1] == '%':
            try:
                sign = 1 if cmd[0] == '+' else -1
                pct = float(cmd[1:-1])
                change = round(jail_mid * pct / 100)
                final_jail = max(jail_min, min(jail_max, final_jail + sign * change))
                print(f"  Jail nastaveny na {final_jail} mesiacov\n")
                print_status(final_jail, final_fine)
            except ValueError:
                print("  Neplatna hodnota.\n")
            continue

        print("  Neznamy prikaz.\n")
        print_status(final_jail, final_fine)

    # ── Finalny vystup ──────────────────────────────────────────────────────────
    reasons_str = " | ".join(f"{l['id']} {l['name']}" for l in selected)
    sentence_str = "LWOP" if lwop else str(final_jail)
    fines_str = str(final_fine)

    result = (
        f"Dohoda o vině a trestu | "
        f"Jméno: {name_p} | "
        f"DOB: {dob} | "
        f"Důvod: {reasons_str} | "
        f"Trest: {sentence_str} měsíců jail | "
        f"Pokuty/a: ${fines_str} | "
        f"Vězení: Boilingbroke Penitentiary | "
        f"Podpis Příslušníka: {signature} | "
        f"Podpis pachatele: {jail_signature}"
    )

    print("\n" + "="*80)
    print("VYSLEDOK:")
    print("="*80)
    print(result)
    print("="*80 + "\n")

    return result


if __name__ == "__main__":
    dovat = main()