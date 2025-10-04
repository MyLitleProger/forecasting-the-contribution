import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Калькулятор вклада", layout="wide")
st.title("🏦 Калькулятор накопительного вклада")

# === Ввод данных ===
col1, col2 = st.columns(2)

with col1:
    initial_amount = st.number_input("Начальная сумма (руб.)", min_value=0, value=0, step=5000)
    monthly_deposit = st.number_input("Ежемесячный вклад (руб.)", min_value=0, value=50000, step=5000)
    years = st.number_input("Срок вклада (лет)", min_value=1, max_value=50, value=3)

with col2:
    st.subheader("Процентные ставки по годам")
    rates = {}
    for y in range(years):
        # Умное значение по умолчанию: снижается, но не ниже 7%
        default_rate = max(7.0, 16.0 - y * 3.0)
        rate = st.number_input(
            f"Ставка, год {y + 1} (% годовых)",
            min_value=0.0, max_value=100.0,
            value=float(default_rate),
            step=0.5,
            key=f"rate_{y}"
        )
        rates[y + 1] = rate / 100

    st.subheader("Инфляция по годам")
    inflation_enabled = st.checkbox("Учитывать инфляцию по годам")
    inflations = {}
    if inflation_enabled:
        for y in range(years):
            # Инфляция по умолчанию — 4%
            default_inf = 4.0
            inf = st.number_input(
                f"Инфляция, год {y + 1} (%)",
                min_value=0.0, max_value=100.0,
                value=float(default_inf),
                step=0.5,
                key=f"inf_{y}"
            )
            inflations[y + 1] = inf / 100
    else:
        for y in range(years):
            inflations[y + 1] = 0.0

# === Расчёт накоплений ===
months_total = years * 12
balance = initial_amount
history = []

for month in range(1, months_total + 1):
    current_year = (month - 1) // 12 + 1
    annual_rate = rates.get(current_year, list(rates.values())[-1])
    monthly_rate = annual_rate / 12

    interest = balance * monthly_rate
    balance += interest
    balance += monthly_deposit

    history.append({
        "Месяц": month,
        "Год": current_year,
        "Сумма до вклада": balance - monthly_deposit,
        "Начислено %": interest,
        "Вклад": monthly_deposit,
        "Баланс": balance
    })

df = pd.DataFrame(history)

# === Расчёт инфляции по годам ===
inflation_cumulative = 1.0
monthly_inflation_factors = []

for month in range(1, months_total + 1):
    current_year = (month - 1) // 12 + 1
    annual_inflation = inflations.get(current_year, list(inflations.values())[-1])
    monthly_inflation = (1 + annual_inflation) ** (1/12) - 1
    inflation_cumulative *= (1 + monthly_inflation)
    monthly_inflation_factors.append(inflation_cumulative)

df["Инфляц. множитель"] = monthly_inflation_factors
df["Реальный баланс"] = df["Баланс"] / df["Инфляц. множитель"]

# === Реальный прирост за месяц ===
df["Реальный прирост"] = df["Реальный баланс"].diff()
df.loc[0, "Реальный прирост"] = df.loc[0, "Реальный баланс"] - (initial_amount / df.loc[0, "Инфляц. множитель"])

# === Итоговые метрики ===
total_deposited = initial_amount + monthly_deposit * months_total
final_balance = df["Баланс"].iloc[-1]
final_real_balance = df["Реальный баланс"].iloc[-1]
profit = final_balance - total_deposited
real_profit = final_real_balance - total_deposited

# Средние ежемесячные начисления
avg_monthly_interest = df["Начислено %"].mean()
avg_real_monthly_growth = df["Реальный прирост"].mean()

# === Вывод результатов ===
st.subheader("📊 Результаты")
col_res1, col_res2, col_res3, col_res4 = st.columns(4)
col_res1.metric("Всего вложено", f"{total_deposited:,.0f} ₽")
col_res2.metric("Итоговая сумма", f"{final_balance:,.0f} ₽")
col_res3.metric("Доход", f"{profit:,.0f} ₽", delta_color="normal")
if inflation_enabled:
    col_res4.metric("Реальный доход", f"{real_profit:,.0f} ₽", delta_color="inverse")

# Дополнительные метрики — средние начисления
st.markdown("### 💰 Средние ежемесячные показатели")
col_m1, col_m2 = st.columns(2)
col_m1.metric("Номинальные начисления", f"{avg_monthly_interest:,.0f} ₽")
if inflation_enabled:
    col_m2.metric("Реальный прирост", f"{avg_real_monthly_growth:,.0f} ₽")

# === График ===
st.subheader("📈 Динамика накоплений")
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df["Месяц"], df["Баланс"], label="Номинальный баланс", color="green")
if inflation_enabled:
    ax.plot(df["Месяц"], df["Реальный баланс"], label="Реальный баланс", color="orange")
ax.set_xlabel("Месяц")
ax.set_ylabel("Сумма (₽)")
ax.legend()
ax.grid(True)
st.pyplot(fig)

# === Таблица ===
with st.expander("Показать таблицу по месяцам"):
    if inflation_enabled:
        display_df = df[[
            "Месяц", "Год", "Вклад", "Начислено %",
            "Баланс", "Реальный баланс", "Реальный прирост"
        ]]
        st.dataframe(display_df.style.format({
            "Вклад": "{:,.0f} ₽",
            "Начислено %": "{:,.0f} ₽",
            "Баланс": "{:,.0f} ₽",
            "Реальный баланс": "{:,.0f} ₽",
            "Реальный прирост": "{:,.0f} ₽"
        }))
    else:
        display_df = df[["Месяц", "Год", "Вклад", "Начислено %", "Баланс"]]
        st.dataframe(display_df.style.format({
            "Вклад": "{:,.0f} ₽",
            "Начислено %": "{:,.0f} ₽",
            "Баланс": "{:,.0f} ₽"
        }))