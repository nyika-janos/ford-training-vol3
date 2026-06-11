# monthly_sales.xlsx sample workbook

A `monthly_sales.xlsx` egy három sheetes minta Excel fájl.

Feltöltéskor ezt a nevet érdemes használni:

```text
landing/monthly_sales.xlsx
```

Így a config tábla három sora is illeszkedik rá, és a program három RAW táblába tölt belőle.

## Sales

```csv
dealer_code,market,sales_date,model,units,revenue
D001,HU,2026-05-01,Focus,3,72000
D002,CZ,2026-05-01,Puma,2,54000
D003,SK,2026-05-02,Kuga,1,39000
D001,HU,2026-05-03,Mustang Mach-E,1,62000
```

## Dealers

```csv
dealer_code,dealer_name,market,city
D001,Budapest Auto,HU,Budapest
D002,Prague Motors,CZ,Prague
D003,Bratislava Ford,SK,Bratislava
```

## MLI Mapping

```csv
model,mli_code,segment
Focus,MLI-100,Passenger Car
Puma,MLI-200,Crossover
Kuga,MLI-300,SUV
Mustang Mach-E,MLI-400,Electric
```
