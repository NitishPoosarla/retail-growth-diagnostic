A retailer asked me two questions: *"Should we scale our ad campaign? And are our
promotions actually worth it?"*

I built an end-to-end diagnostic to answer both — and made "here's what the data
can't tell you" the headline.

What it demonstrates:
• An A/B readout with confidence intervals and power, not just p-values
• A backtest that admits when the model only *barely* beats its baseline
• A counterfactual promo bridge labelled association, not causation
• A break-even tool that turns a conversion lift into scale / hold / cut

Three findings (denominators included):
1. Ads: conversion 2.55% (14,423/564,577) vs 1.79% (420/23,524) → +0.77pp,
~100% powered.
2. Forecast: WAPE 10.39% vs 12.05% seasonal-naive — still winning at Christmas
(14.52% vs 17.12%).
3. Promo: +28% of promo-day revenue from the model, vs 38.8% naively.
Association, not causal.

Full writeup + code: <repo link>

#analytics #ABTesting #DataScience #Forecasting #CausalInference
