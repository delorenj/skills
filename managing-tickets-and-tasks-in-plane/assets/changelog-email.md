Subject: 🚀 Production Release - {{DATE}} - {{FEATURE_COUNT}} Features Deployed

---

Hi Team,

We've just deployed **{{TOTAL_TICKETS}} tickets** ({{TOTAL_POINTS}} story points) to production. Here's what's new:

---

## 🚀 Features

{{#FEATURES}}
### [{{TICKET_ID}}] {{TITLE}}
{{DESCRIPTION_SUMMARY}}

**Impact:** {{IMPACT}}
**Points:** {{POINTS}}

{{/FEATURES}}

---

## 🐛 Bug Fixes

{{#FIXES}}
### [{{TICKET_ID}}] {{TITLE}}
{{DESCRIPTION_SUMMARY}}

**Severity:** {{SEVERITY}}
**Points:** {{POINTS}}

{{/FIXES}}

---

## 🔧 Technical Improvements

{{#IMPROVEMENTS}}
### [{{TICKET_ID}}] {{TITLE}}
{{DESCRIPTION_SUMMARY}}

**Benefit:** {{BENEFIT}}
**Points:** {{POINTS}}

{{/IMPROVEMENTS}}

---

## 📊 Sprint Metrics

**Sprint:** Sprint {{SPRINT_NUMBER}}
**Sprint Goal:** {{SPRINT_GOAL}}

**Delivery:**
- Total Tickets: {{TOTAL_TICKETS}}
- Story Points Delivered: {{TOTAL_POINTS}}
- Features: {{FEATURE_COUNT}}
- Bug Fixes: {{FIX_COUNT}}
- Tech Improvements: {{IMPROVEMENT_COUNT}}

**Velocity:**
- Planned: {{PLANNED_POINTS}} points
- Delivered: {{DELIVERED_POINTS}} points
- Completion: {{COMPLETION_PCT}}%

---

## 🔗 Links

- **Sprint Plan:** {{SPRINT_PLAN_URL}}
- **Plane Board:** https://plane.internal.intelliforia.com/intelliforia/projects/{{PROJECT_ID}}
- **Production:** {{PRODUCTION_URL}}
- **Staging:** {{STAGING_URL}}

---

## 🎯 Next Sprint Preview

**Sprint {{NEXT_SPRINT_NUMBER}} starts {{NEXT_SPRINT_START_DATE}}**

**Focus Areas:**
{{#NEXT_SPRINT_FOCUS}}
- {{FOCUS_AREA}}
{{/NEXT_SPRINT_FOCUS}}

**Sprint Planning:** {{SPRINT_PLANNING_DATE}} at {{SPRINT_PLANNING_TIME}}

---

## 📝 Release Notes

{{#DETAILED_CHANGES}}
### {{COMPONENT_NAME}}

{{#CHANGES}}
- {{CHANGE_DESCRIPTION}}
{{/CHANGES}}

{{/DETAILED_CHANGES}}

---

## 🙏 Acknowledgments

Thanks to everyone who contributed to this release:

{{#CONTRIBUTORS}}
- **{{NAME}}**: {{TICKETS_COMPLETED}} tickets, {{POINTS_DELIVERED}} points
{{/CONTRIBUTORS}}

---

Questions? Reply to this email or check Plane for detailed ticket information.

Best,
**IntelliForia Development Team**
(via Claude Code Automation)

---

*This changelog was automatically generated from Plane tickets. [View Sprint Board](https://plane.internal.intelliforia.com/intelliforia/projects/{{PROJECT_ID}})*
