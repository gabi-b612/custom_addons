18.0.1.0.2 (Date: 02 Oct,2025)
-------------------------------

Updated The issue in "Products with negative/zero quantities still showing when "Disable Negative Quantity Products" is enabled".
Solved the issue with Stock Location filtering Logic.

How Threshold -1000 Works:
With threshold set to -1000, products will only show warning when stock goes below -1000. This means:

Products with qty > -1000 → ✅ Can be added
Products with qty <= -1000 → ⚠️ Warning shown

18.0.1.0.3 (Date: 07 Oct,2025)
-------------------------------

Optimized performance ( removed ORM call logic )

18.0.1.0.4 (Date: 08 Oct,2025)
-------------------------------

Updated threshold system, now works 100% real-time for both:

✅ Product card clicks
✅ Numpad quantity entry