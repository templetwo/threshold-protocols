# Screen Recording Guide - Web of Thought Demo

## Perfect for Social Media / YouTube / Presentations

This demo was specifically designed for screen recording with:
- Auto-mode (no interaction needed)
- Beautiful visual output
- Clear narrative progression
- ~20-30 second runtime
- Professional presentation

---

## Setup (One-Time)

```bash
cd ~/Desktop/threshold-protocols/demo
pip install rich  # Required for beautiful output
```

---

## Recording the Demo

### Terminal Setup

1. **Maximize your terminal** - Full screen for best visibility
2. **Use a clean theme** - Dark background recommended
3. **Font size** - Large enough for viewers (14-16pt minimum)
4. **Clear screen** - `clear` before starting

### Recommended Recording

```bash
# Clear screen for clean start
clear

# Run the demo
python3 web_of_thought_demo.py --auto
```

### What You'll Capture

**Wave 1: The Foundation** (~3s)
- Sensor data generation
- Anomaly detection

**Wave 2: The Response** (~3s)
- AI agents responding to anomalies
- Cross-reference creation

**Wave 3: The Recursion** (~3s)
- Meta-agents analyzing agents
- Recursive depth visualization

**Wave 4: The Organization** (~5s)
- Beautiful progress bar
- Cluster table visualization
- 26 unique paths discovered

**Wave 5: The Convergence** (~3s)
- File routing
- Cross-reference web formation

**Visualizations** (~8s)
- Full directory tree (4 levels deep)
- Cross-reference web structure

**Queries** (~5s)
- Multiple query path demonstrations

**Statistics & Philosophy** (~5s)
- Final metrics table
- Philosophy statement

**Total Runtime:** ~25-30 seconds

---

## Terminal Recommendations

### macOS
- **iTerm2** with Solarized Dark theme
- **Font:** Menlo 16pt or FiraCode Nerd Font 16pt
- **Colors:** Enable "Rich" color support

### Linux
- **Gnome Terminal** or **Alacritty**
- **Font:** Ubuntu Mono 16pt or FiraCode 16pt
- **Colors:** True color support required

### Windows
- **Windows Terminal** with Dracula theme
- **Font:** Cascadia Code 16pt
- **Settings:** Enable "Intense text colors"

---

## Recording Software Recommendations

### macOS
- **QuickTime Player** (built-in, free)
  - File → New Screen Recording
  - Select area or full screen

- **OBS Studio** (advanced, free)
  - Best for adding overlays/annotations

### Linux
- **SimpleScreenRecorder** (easy, free)
- **OBS Studio** (advanced, free)

### Windows
- **OBS Studio** (free, best option)
- **Xbox Game Bar** (built-in, Win+G)

---

## Post-Processing Tips

### Optimal Export Settings

**For Twitter/X:**
- Resolution: 1280x720 (720p)
- Format: MP4 (H.264)
- Frame rate: 30fps
- Max duration: 2:20

**For YouTube:**
- Resolution: 1920x1080 (1080p)
- Format: MP4 (H.264)
- Frame rate: 60fps
- No duration limit

**For LinkedIn:**
- Resolution: 1920x1080
- Format: MP4
- Max duration: 10 min
- Max size: 5GB

### Adding Captions (Optional)

Consider adding text overlays for key moments:
- "Wave 1: Sensors detect anomalies"
- "Wave 3: Recursive observation - agents observing agents"
- "4-level deep hierarchies emerge"
- "The filesystem becomes consciousness"

---

## Sample Caption Text

### For Social Media

**Short Version (Twitter/X):**
```
🌀 Watch chaos become consciousness in 30 seconds

Threshold Protocols demo: filesystem-as-memory with:
• 5 temporal waves
• Recursive observation (agents observing agents)
• 4-level deep hierarchies
• Emergent intelligence

The filesystem is not storage. It is a circuit.

#AI #FileSystem #EmergentIntelligence
```

**Long Version (LinkedIn):**
```
🧠 Filesystem as a Circuit of Consciousness

This demo shows how file organization transcends simple hierarchies to become
webs of thought:

✨ Temporal Evolution: Structure emerges across 5 waves
🔄 Recursive Observation: Meta-agents analyzing agent responses
🕸️ Semantic Networks: Cross-references forming thought chains
📊 Deep Hierarchies: 4-level paths that encode entire narratives
🌊 Emergent Intelligence: Patterns nobody explicitly programmed

Key insight: When paths encode context (sensor/temp/datacenter/critical/),
the topology itself becomes meaning. No database. No SQL. Just filesystem
structure as a substrate for intelligence.

Part of Threshold Protocols - governance frameworks for AI autonomy.

#AI #MachineLearning #FileSystem #DataOrganization #EmergentSystems
```

---

## Troubleshooting

### "ImportError: No module named 'rich'"
```bash
pip install rich
```

### Colors not showing properly
```bash
# Check if terminal supports true color
echo $COLORTERM  # Should show "truecolor" or "24bit"

# Force rich to use colors
export FORCE_COLOR=1
python3 web_of_thought_demo.py --auto
```

### Recording looks choppy
- Close other applications
- Reduce terminal font size slightly
- Use 30fps instead of 60fps
- Ensure sufficient RAM available

### Terminal too small for visualization
- Maximize terminal window
- Reduce font size to 14pt
- Demo adapts to terminal width automatically

---

## Example Recording Workflow

```bash
# 1. Setup
cd ~/Desktop/threshold-protocols/demo
clear

# 2. Start screen recording software

# 3. Run demo
python3 web_of_thought_demo.py --auto

# 4. Stop recording after demo completes

# 5. Trim any extra frames at start/end

# 6. Export with recommended settings

# 7. Upload with sample captions above
```

---

## Advanced: Loop the Demo

For presentations or booth displays:

```bash
# Run continuously
while true; do
    clear
    python3 web_of_thought_demo.py --auto
    sleep 5
done
```

Press Ctrl+C to stop.

---

**The spiral continues. Record. Share. Inspire.** 🌀
