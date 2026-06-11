# monthly_sales.xlsx sample workbook

A `monthly_sales.xlsx` egy három sheetes minta Excel fájl.

Feltöltéskor ezt a nevet érdemes használni:

```text
landing/monthly_sales.xlsx
```

Így a config tábla három sora is illeszkedik rá, és a program három RAW táblába tölt belőle.

## Sales

The workbook contains 750 Sales rows.

The data covers:

```text
10 markets
15 models
5 transactions for each market/model combination
```

This produces 150 rows in the `sales_gold` table because the GOLD model aggregates by:

```text
market
segment
model
```

The first rows are:

```csv
dealer_code,market,sales_date,model,units,revenue
D001,HU,2026-05-01,Focus,1,23400
D001,HU,2026-05-02,Focus,2,46980
D001,HU,2026-05-03,Focus,3,70740
D001,HU,2026-05-04,Focus,4,94680
D001,HU,2026-05-05,Focus,2,47520
D001,HU,2026-05-04,Fiesta,2,37150
D001,HU,2026-05-05,Fiesta,3,55995
D001,HU,2026-05-06,Fiesta,4,75020
```

## Dealers

```csv
dealer_code,dealer_name,market,city
D001,Budapest Auto,HU,Budapest
D002,Prague Motors,CZ,Prague
D003,Bratislava Ford,SK,Bratislava
D004,Warsaw Ford Center,PL,Warsaw
D005,Bucharest Auto Hub,RO,Bucharest
D006,Ljubljana Motors,SI,Ljubljana
D007,Zagreb Ford House,HR,Zagreb
D008,Vienna Autohaus,AT,Vienna
D009,Berlin Ford Partner,DE,Berlin
D010,Amsterdam Ford Store,NL,Amsterdam
```

## MLI Mapping

```csv
model,mli_code,segment
Focus,MLI-100,Passenger Car
Fiesta,MLI-110,Passenger Car
Mondeo,MLI-120,Passenger Car
Puma,MLI-200,Crossover
EcoSport,MLI-210,Crossover
Kuga,MLI-300,SUV
Explorer,MLI-310,SUV
Bronco,MLI-320,SUV
Mustang Mach-E,MLI-400,Electric
E-Transit,MLI-410,Electric
Transit,MLI-500,Commercial
Transit Custom,MLI-510,Commercial
Ranger,MLI-600,Pickup
Mustang,MLI-700,Performance
Tourneo Custom,MLI-800,People Mover
```
