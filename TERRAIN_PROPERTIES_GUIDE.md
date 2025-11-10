# Terrain Properties Guide

## Complete Terrain Type Reference

### 🌊 Water
**Color:** `#4682B4` (Steel Blue)  
**Flammability:** Non-flammable  
**Key Properties:**
- Ignition Threshold: 999.0 (Impossible)
- Spread Probability: 0.0%
- Max Burn Duration: 0 ticks
- Moisture: 100%
- **Behavior:** Acts as permanent firebreak, cannot burn under any conditions

---

### 🏖️ Beach/Sand
**Color:** `#D2B48C` (Tan)  
**Flammability:** Non-flammable  
**Key Properties:**
- Ignition Threshold: 0.95 (Very Hard)
- Spread Probability: 5%
- Max Burn Duration: 1 tick
- Moisture: 50%
- **Behavior:** Sand doesn't burn; minimal fire spread possible from debris

---

### 🏜️ Bare Ground
**Color:** `#D2B48C` (Tan/Brown)  
**Flammability:** Very Low  
**Key Properties:**
- Ignition Threshold: 0.85 (Hard)
- Spread Probability: 10%
- Max Burn Duration: 1 tick
- Moisture: 20%
- Fuel Consumption: 80% per tick
- **Behavior:** Minimal vegetation, acts as partial firebreak

---

### 🏙️ Urban
**Color:** `#808080` (Gray)  
**Flammability:** Very Low  
**Key Properties:**
- Ignition Threshold: 0.9 (Very Hard)
- Spread Probability: 10%
- Max Burn Duration: 12 ticks
- Moisture: 20%
- Fuel Consumption: 5% per tick
- Heat Generation: 30%
- **Behavior:** Buildings can burn but spread very slowly; concrete/asphalt resistant

---

### 🏜️ Desert
**Color:** `#D2B48C` (Sandy)  
**Flammability:** Low  
**Key Properties:**
- Ignition Threshold: 0.8 (Hard)
- Spread Probability: 20%
- Max Burn Duration: 2 ticks
- Moisture: 20%
- Fuel Consumption: 60% per tick
- **Behavior:** Sparse vegetation, quick burn through when ignited

---

### 🌾 Agriculture
**Color:** `#DAA520` (Goldenrod)  
**Flammability:** Moderate  
**Key Properties:**
- Ignition Threshold: 0.4 (Moderate)
- Spread Probability: 60%
- Max Burn Duration: 4 ticks
- Moisture: 50%
- Fuel Consumption: 20% per tick
- Heat Generation: 60%
- **Behavior:** Cropland burns moderately; depends on harvest season

---

### 🌿 Shrub
**Color:** `#9ACD32` (Yellow Green)  
**Flammability:** Moderate-High  
**Key Properties:**
- Ignition Threshold: 0.35 (Moderately Easy)
- Spread Probability: 75%
- Max Burn Duration: 5 ticks
- Moisture: 60%
- Fuel Consumption: 18% per tick
- Heat Generation: 80%
- **Behavior:** Medium-density vegetation, consistent fire spread

---

### 🌲 Forest
**Color:** `#228B22` (Forest Green)  
**Flammability:** High  
**Key Properties:**
- Ignition Threshold: 0.3 (Easy)
- Spread Probability: 80%
- Max Burn Duration: 8 ticks
- Moisture: 60%
- Fuel Consumption: 12% per tick
- Heat Generation: 90%
- **Behavior:** Dense canopy, sustained burning, high heat output

---

### 🌱 Grass
**Color:** `#90EE90` (Light Green)  
**Flammability:** Very High  
**Key Properties:**
- Ignition Threshold: 0.2 (Very Easy)
- Spread Probability: 95%
- Max Burn Duration: 3 ticks
- Moisture: 50%
- Fuel Consumption: 25% per tick
- Heat Generation: 70%
- **Behavior:** Fast-spreading, quick-burning, flashy fuel

---

## Fire Behavior Comparisons

### Spread Speed (Fastest to Slowest)
1. 🌱 Grass (95%)
2. 🌲 Forest (80%)
3. 🌿 Shrub (75%)
4. 🌾 Agriculture (60%)
5. 🏜️ Desert (20%)
6. 🏙️ Urban (10%)
7. 🏜️ Bare Ground (10%)
8. 🏖️ Beach (5%)
9. 🌊 Water (0%)

### Burn Duration (Longest to Shortest)
1. 🏙️ Urban (12 ticks)
2. 🌲 Forest (8 ticks)
3. 🌿 Shrub (5 ticks)
4. 🌾 Agriculture (4 ticks)
5. 🌱 Grass (3 ticks)
6. 🏜️ Desert (2 ticks)
7. 🏜️ Bare Ground (1 tick)
8. 🏖️ Beach (1 tick)
9. 🌊 Water (0 ticks)

### Ignition Difficulty (Hardest to Easiest)
1. 🌊 Water (999.0 - Impossible)
2. 🏖️ Beach (0.95 - Very Hard)
3. 🏙️ Urban (0.9 - Very Hard)
4. 🏜️ Bare Ground (0.85 - Hard)
5. 🏜️ Desert (0.8 - Hard)
6. 🌾 Agriculture (0.4 - Moderate)
7. 🌿 Shrub (0.35 - Moderately Easy)
8. 🌲 Forest (0.3 - Easy)
9. 🌱 Grass (0.2 - Very Easy)

## Environmental Modifiers

All terrain types are affected by:

### ☀️ Temperature
- Base: 20°C
- Effect: +2% spread probability per degree above 20°C
- Example: At 30°C, fire spreads 20% faster

### 💧 Humidity
- Base: 50%
- Effect: -1% spread probability per % above 50%
- Example: At 70% humidity, fire spreads 20% slower

### 💨 Wind
- Effect: Increases spread in wind direction
- Wind alignment factor: up to 50% increase with wind
- Against wind: minimum 10% spread chance

### 🌧️ Rain
- Effect: -80% spread probability per unit rain
- Heavy rain can extinguish active fires
- Increases cell moisture content

## Fire Simulation Tips

### Creating Effective Firebreaks
1. **Best Natural Barriers:** Water bodies (100% effective)
2. **Good Barriers:** Urban areas, bare ground strips
3. **Partial Barriers:** Agriculture fields (width matters)
4. **Poor Barriers:** Desert, beach (fire can jump)

### High-Risk Scenarios
1. **Grass + Wind + Low Humidity:** Extremely rapid spread
2. **Forest + High Temperature:** Long-duration, intense fires
3. **Urban-Wildland Interface:** Structures at risk from wildfire

### Simulation Strategy
1. **Start fires in grass** for fast-moving scenarios
2. **Use forest** for sustained, realistic wildfires
3. **Place urban/water** to test firebreak effectiveness
4. **Mix terrains** for realistic landscape simulations

## Real-World Applications

### Wildfire Risk Assessment
- **High Risk:** Dense forest with grass understory
- **Moderate Risk:** Shrubland with scattered agriculture
- **Low Risk:** Urban areas with proper defensible space

### Fire Management Planning
- **Prescribed Burns:** Effective in grass and shrub terrains
- **Fuel Reduction:** Critical in forest and shrub interfaces
- **Firebreak Placement:** Use terrain advantages (roads, water, bare ground)

## Technical Notes

### Moisture Dynamics
- **Initial moisture** set by terrain type
- **Decreases** as cell burns (moisture_loss_rate)
- **Affected by** rain and humidity
- **Influences** ignition threshold and spread

### Fuel Consumption
- **Fuel load** starts at 1.0 (or 0.0 for non-flammable)
- **Depletes** based on fuel_consumption_rate
- **Fire burns out** when fuel < 0.1
- **Terrain type** determines consumption speed

### Heat Generation
- **Affects** neighboring cell ignition probability
- **Higher values:** More intense fire, more likely to spread
- **Forest fires:** Highest heat (90%)
- **Urban fires:** Lowest heat (30%)

---

## Quick Reference Table

| Terrain | Color | Flammable? | Spread % | Duration | Ignition | Best Use |
|---------|-------|------------|----------|----------|----------|----------|
| Water | Blue | ❌ No | 0% | 0 | 999.0 | Firebreak |
| Beach | Tan | ❌ No | 5% | 1 | 0.95 | Barrier |
| Bare Ground | Brown | ✅ Yes | 10% | 1 | 0.85 | Firebreak |
| Urban | Gray | ✅ Yes | 10% | 12 | 0.90 | WUI Testing |
| Desert | Sandy | ✅ Yes | 20% | 2 | 0.80 | Sparse Fire |
| Agriculture | Gold | ✅ Yes | 60% | 4 | 0.40 | Mixed Use |
| Shrub | Yellow-Green | ✅ Yes | 75% | 5 | 0.35 | Mid Fuel |
| Forest | Dark Green | ✅ Yes | 80% | 8 | 0.30 | Crown Fire |
| Grass | Light Green | ✅ Yes | 95% | 3 | 0.20 | Flash Fuel |

---

**Legend:**
- ✅ Flammable: Can catch and spread fire
- ❌ Non-flammable: Cannot burn
- Spread %: Base probability of spreading to adjacent cells
- Duration: Ticks cell burns before becoming ash
- Ignition: Threshold for initial ignition (lower = easier)
