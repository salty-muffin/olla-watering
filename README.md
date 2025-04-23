# olla-watering
automatic olla filling with a rp pico, valves &amp; sensors


# plan

JSON on every Pico that contains: 
- time slot, when the watering program shall be started
- maximum filling for each valve
- overfill time in seconds (time the valve stays open after the sensor registers `full`)

# filling program
For each Valve 
- average sensor signal over X seconds (long) to estimate if the olla really needs filling
- after valve is opened, a shorter peridod of time is used to estimate the new `full` state
- then the valve stays open for X seconds, as set in the JSON to ensure the sensor will not register an empty olla too soon. 