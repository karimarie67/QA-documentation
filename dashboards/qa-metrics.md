# 📊 QA Metrics Dashboard

> **Automated Quality Gate Report**

**Last Updated:** Tuesday, September 22, 2026 at 2:33 PM | **Env:** STAGING | **Branch:** issue-6/genericize-template
**Run:** [#173](https://github.com/karimarie67/QA-documentation/actions/runs/35767617795)

---

## 🎯 Executive Summary

| Metric | Current Value | Status |
|--------|---------------|----------------|
| **Pass Rate** | **16.0%** | 🔴 Attention |
| **Duration** | **1m 11s** | ✅ Good |
| **Total Tests** | 25 | 4 Pass / 21 Fail |
| **Functional** | 25 Tests | ✅ Active |

---

### 🌐 Browser Breakdown

| Project | Pass Rate | Status |
|---|---|---|
| **staging** | 16.0% | 🔴 |


---

## 🔍 Detailed Test Results

### 🔥 Smoke Tests
> *No tests found in this category* 


### 🧩 Functional Tests (Errors, Docs, Search)
| Test Name | Status | Duration | Project |
|-----------|--------|----------|---------|
| 404 page displays appropriate error message | ❌ failed | 2.5s | staging |
| Broken documentation link returns appropriate error | ❌ failed | 15.1s | staging |
| Invalid search query handles gracefully | ❌ failed | 2.5s | staging |
| Malformed URL redirects or shows error appropriately | ✅ passed | <1s | staging |
| Broken external links are identified | ❌ failed | 2.4s | staging |
| Form validation errors display correctly | ❌ failed | 2.5s | staging |
| Download links return valid HTTP status codes | ❌ failed | 2.6s | staging |
| Download file names are correct format | ❌ failed | 2.5s | staging |
| Version selector displays available versions | ❌ failed | 2.5s | staging |
| Download page displays file sizes | ❌ failed | 2.5s | staging |

*... and 15 more tests*


---

## 📈 History (Last 10 Runs)
| Date | Pass Rate | Duration | Failures |
|------|-----------|----------|----------|
| Sep 22 | 16.0% | 1m 11s | 21 |

---
