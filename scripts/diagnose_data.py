#!/usr/bin/env python3
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_data import _find_source, _read_headered_exact, _read_positional
from cmed import read_cmed_csv
from common import digits
from schemas import BULA_DOCUMENTO_COLUMNS, BULA_PRODUTO_COLUMNS, IRREGULAR_COLUMNS, MEDICINES_COLUMNS
from source_registry import SOURCES


def main() -> None:
    root = SCRIPT_DIR.parent
    raw = root / "public" / "fontes"
    print("MEDICAMENTO ABERTO — DIAGNÓSTICO DOS 6 CSVs")
    print("=" * 100)
    if not raw.exists():
        raise SystemExit(f"Diretório não encontrado: {raw}")

    frames = {}
    for source in SOURCES:
        path = _find_source(raw, source)
        if path is None:
            print(f"[ERRO] {source.key}: ausente. Aceitos: {', '.join(source.filenames)}")
            continue
        try:
            if source.key in {"cmed_consumidor", "cmed_governo"}:
                frame, metadata = read_cmed_csv(path)
                extra = f" · cabeçalho físico na linha {metadata.headerLine}"
            elif source.key == "medicamentos":
                frame = _read_headered_exact(path, MEDICINES_COLUMNS)
                extra = ""
            elif source.key == "irregulares":
                frame = _read_headered_exact(path, IRREGULAR_COLUMNS)
                extra = ""
            elif source.key == "bula_produto":
                frame = _read_positional(path, BULA_PRODUTO_COLUMNS)
                extra = " · sem cabeçalho; nomes funcionais internos aplicados"
            elif source.key == "bula_documento":
                frame = _read_positional(path, BULA_DOCUMENTO_COLUMNS)
                extra = " · sem cabeçalho; nomes funcionais internos aplicados"
            else:
                continue
            frames[source.key] = frame
            print(f"[OK] {source.key:<20} {path.name:<50} linhas={len(frame):>8,} colunas={len(frame.columns):>3}{extra}")
        except Exception as exc:
            print(f"[ERRO] {source.key}: {exc}")

    if "medicamentos" not in frames:
        raise SystemExit(2)

    med = frames["medicamentos"]
    dedup = med.drop_duplicates()
    reg_digits = dedup["NUMERO_REGISTRO_PRODUTO"].map(digits)
    reg_lengths = Counter(map(len, reg_digits))
    valid_reg = reg_digits[reg_digits.map(len) == 9]
    valid_reg_set = set(valid_reg)

    print("\nBASE PRINCIPAL — PRODUTOS")
    print("-" * 100)
    print(f"Linhas recebidas:                         {len(med):>10,}")
    print(f"Duplicatas exatas:                        {int(med.duplicated().sum()):>10,}")
    print(f"Linhas distintas/produtos lógicos:       {len(dedup):>10,}")
    print(f"Registros de produto válidos (9 dígitos):{len(valid_reg):>10,}")
    print(f"Registros de produto únicos (9 dígitos): {valid_reg.nunique():>10,}")
    print(f"Sem número de registro:                   {reg_lengths.get(0, 0):>10,}")
    print(f"Comprimento diferente de 0/9:             {sum(v for k,v in reg_lengths.items() if k not in (0,9)):>10,}")
    print("Distribuição por comprimento:", dict(sorted(reg_lengths.items())))

    for key in ("cmed_consumidor", "cmed_governo"):
        if key not in frames:
            continue
        frame = frames[key]
        regs = frame["REGISTRO"].map(digits)
        lengths = Counter(map(len, regs))
        valid = regs[regs.map(len) == 13]
        bases = valid.str[:9]
        print(f"\n{key.upper()} — APRESENTAÇÕES / CMED")
        print("-" * 100)
        print(f"Linhas:                                    {len(frame):>10,}")
        print(f"REGISTRO de apresentação (13 dígitos):     {len(valid):>10,}")
        print(f"REGISTRO de apresentação únicos:           {valid.nunique():>10,}")
        print(f"CÓDIGO GGREM únicos:                        {frame['CÓDIGO GGREM'].astype(str).str.strip().nunique():>10,}")
        print(f"Bases de produto (primeiros 9) distintas:   {bases.nunique():>10,}")
        print(f"Bases de produto encontradas na principal:  {sum(base in valid_reg_set for base in bases):>10,}")
        print("Distribuição REGISTRO por comprimento:", dict(sorted(lengths.items())))

    if "irregulares" in frames:
        irr_regs = frames["irregulares"]["REGISTRO"].map(digits)
        irr_lengths = Counter(map(len, irr_regs))
        print("\nFISCALIZAÇÃO — CAMPO REGISTRO")
        print("-" * 100)
        print("Distribuição por comprimento:", dict(sorted(irr_lengths.items())))
        print("Regra aplicada: somente valores com exatamente 9 dígitos são relacionados ao medicamento.")

    known_regs = valid_reg_set
    known_proc = {digits(v) for v in med["NUMERO_PROCESSO"] if digits(v)}

    if "bula_produto" in frames:
        bp = frames["bula_produto"]
        r = [digits(v) for v in bp["NUMERO_REGISTRO_PRODUTO"] if digits(v)]
        p = [digits(v) for v in bp["NUMERO_PROCESSO"] if digits(v)]
        print("\nBULA_PRODUTO — ÚLTIMA ATUALIZAÇÃO DO BULARIO")
        print("-" * 100)
        print(f"NUMERO_REGISTRO_PRODUTO -> base principal: {sum(v in known_regs for v in r):,}/{len(r):,} correspondências")
        print(f"NUMERO_PROCESSO -> base principal:          {sum(v in known_proc for v in p):,}/{len(p):,} correspondências")

    if "bula_documento" in frames:
        bd = frames["bula_documento"]
        p = [digits(v) for v in bd["NUMERO_PROCESSO"] if digits(v)]
        print("\nBULA_DOCUMENTO — HISTÓRICO DO BULARIO")
        print("-" * 100)
        print(f"NUMERO_PROCESSO -> base principal: {sum(v in known_proc for v in p):,}/{len(p):,} correspondências")


if __name__ == "__main__":
    main()
