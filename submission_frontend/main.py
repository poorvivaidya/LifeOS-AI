import os
import json
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

import vertexai
from vertexai.preview.reasoning_engines import ReasoningEngine
from google.adk.sessions import VertexAiSessionService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard")

app = FastAPI(title="LifeOS AI Dashboard Service")

# Read GCP Project and Reasoning Engine ID from environment variables
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT") or os.environ.get("PROJECT_ID")
AGENT_RUNTIME_ID = os.environ.get("AGENT_RUNTIME_ID")
LOCATION = os.environ.get("GCP_REGION") or os.environ.get("LOCATION") or os.environ.get("GOOGLE_CLOUD_LOCATION", "us-east1")

# Session service singleton placeholder
service = None

def get_session_service() -> VertexAiSessionService:
    global service
    if service is not None:
        return service
    
    proj = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT") or os.environ.get("PROJECT_ID")
    runtime_id = os.environ.get("AGENT_RUNTIME_ID")
    loc = os.environ.get("GCP_REGION") or os.environ.get("LOCATION") or os.environ.get("GOOGLE_CLOUD_LOCATION", "us-east1")
    
    if not proj or not runtime_id:
        raise HTTPException(
            status_code=500, 
            detail="GCP_PROJECT/PROJECT_ID and AGENT_RUNTIME_ID environment variables must be configured."
        )
    try:
        vertexai.init(project=proj, location=loc)
        service = VertexAiSessionService(
            project=proj,
            location=loc,
            agent_engine_id=runtime_id
        )
        return service
    except Exception as e:
        logger.error(f"Failed to initialize VertexAiSessionService: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize VertexAiSessionService: {str(e)}"
        )

# HTML Content of the beautiful manager dashboard
HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LifeOS AI Dashboard</title>
    <!-- Google Fonts: Outfit -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <!-- FontAwesome for icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-color: #08090c;
            --card-bg: rgba(255, 255, 255, 0.03);
            --card-border: rgba(255, 255, 255, 0.07);
            --card-border-hover: rgba(255, 255, 255, 0.15);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --primary-glow: rgba(99, 102, 241, 0.12);
            --accent-glow: rgba(236, 72, 153, 0.12);
            
            --success-color: #10b981;
            --success-bg: rgba(16, 185, 129, 0.1);
            --success-border: rgba(16, 185, 129, 0.2);
            
            --danger-color: #ef4444;
            --danger-bg: rgba(239, 68, 68, 0.1);
            --danger-border: rgba(239, 68, 68, 0.2);
            
            --info-color: #3b82f6;
            --info-bg: rgba(59, 130, 246, 0.1);
            --info-border: rgba(59, 130, 246, 0.2);
            
            --transition-smooth: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
            display: flex;
            flex-direction: column;
        }

        /* Radial Glow Backgrounds */
        body::before {
            content: '';
            position: fixed;
            top: -10%;
            left: -10%;
            width: 50vw;
            height: 50vw;
            background: radial-gradient(circle, var(--primary-glow) 0%, transparent 70%);
            z-index: -1;
            pointer-events: none;
            filter: blur(80px);
        }

        body::after {
            content: '';
            position: fixed;
            bottom: -10%;
            right: -10%;
            width: 50vw;
            height: 50vw;
            background: radial-gradient(circle, var(--accent-glow) 0%, transparent 70%);
            z-index: -1;
            pointer-events: none;
            filter: blur(80px);
        }

        header {
            width: 100%;
            padding: 20px 40px;
            background: rgba(8, 9, 12, 0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--card-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 50;
        }

        .logo-container {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-icon {
            font-size: 24px;
            background: linear-gradient(135deg, #6366f1, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 2px 8px rgba(99, 102, 241, 0.3));
        }

        .logo-text {
            font-size: 20px;
            font-weight: 700;
            letter-spacing: -0.5px;
            background: linear-gradient(to right, #ffffff, #d1d5db);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.05);
            padding: 6px 14px;
            border-radius: 9999px;
            border: 1px solid var(--card-border);
            font-size: 13px;
            font-weight: 500;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: var(--success-color);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--success-color);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        main {
            max-width: 1200px;
            width: 100%;
            margin: 40px auto;
            padding: 0 24px;
            flex-grow: 1;
        }

        /* Stats Section */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            transition: var(--transition-smooth);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .stat-card:hover {
            border-color: var(--card-border-hover);
            transform: translateY(-2px);
        }

        .stat-label {
            font-size: 14px;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .stat-val {
            font-size: 36px;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -1px;
        }

        /* Dashboard Content */
        .section-header {
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .section-title {
            font-size: 22px;
            font-weight: 600;
            letter-spacing: -0.5px;
        }

        .refresh-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            color: var(--text-primary);
            padding: 8px 16px;
            border-radius: 8px;
            font-family: inherit;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: var(--transition-smooth);
        }

        .refresh-btn:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--card-border-hover);
        }

        /* Cards List */
        .cards-list {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
        }

        .expense-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            transition: var(--transition-smooth);
            display: flex;
            flex-direction: column;
            gap: 20px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 24px rgba(0,0,0,0.2);
        }

        .expense-card:hover {
            border-color: var(--card-border-hover);
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(99, 102, 241, 0.08);
        }

        /* Card Header */
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }

        .submitter-info {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .submitter-email {
            font-size: 16px;
            font-weight: 600;
            color: #ffffff;
        }

        .expense-date {
            font-size: 13px;
            color: var(--text-secondary);
        }

        .expense-amount {
            font-size: 26px;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #ffffff, #e5e7eb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Card Details */
        .card-details {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .expense-desc {
            font-size: 14px;
            line-height: 1.5;
            color: var(--text-secondary);
        }

        .meta-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .badge {
            font-size: 12px;
            font-weight: 500;
            padding: 4px 10px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
            border: 1px solid transparent;
        }

        .badge-category {
            background: var(--info-bg);
            color: var(--info-color);
            border-color: var(--info-border);
        }

        .badge-session {
            background: rgba(255, 255, 255, 0.03);
            color: var(--text-secondary);
            border-color: var(--card-border);
            font-family: monospace;
        }

        /* Card Actions */
        .card-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 8px;
            gap: 12px;
        }

        .secondary-actions {
            display: flex;
            gap: 12px;
        }

        .btn {
            font-family: inherit;
            font-size: 14px;
            font-weight: 600;
            padding: 10px 20px;
            border-radius: 10px;
            cursor: pointer;
            transition: var(--transition-smooth);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            border: 1px solid transparent;
            outline: none;
            position: relative;
        }

        .btn-view-review {
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--card-border);
            color: var(--text-primary);
        }

        .btn-view-review:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--card-border-hover);
        }

        .btn-approve {
            background: var(--success-color);
            color: #08090c;
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
        }

        .btn-approve:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
            background: #059669;
        }

        .btn-reject {
            background: transparent;
            border-color: var(--danger-color);
            color: var(--danger-color);
        }

        .btn-reject:hover:not(:disabled) {
            background: var(--danger-bg);
            transform: translateY(-2px);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Loading spinner */
        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid transparent;
            border-top-color: currentColor;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            display: none;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .btn.loading .spinner {
            display: inline-block;
        }

        .btn.loading .btn-text {
            display: none;
        }

        /* Slide-out Panel */
        .drawer-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(4px);
            z-index: 100;
            opacity: 0;
            visibility: hidden;
            transition: var(--transition-smooth);
        }

        .drawer-overlay.open {
            opacity: 1;
            visibility: visible;
        }

        .drawer {
            position: fixed;
            top: 0;
            right: -500px;
            width: 100%;
            max-width: 500px;
            height: 100vh;
            background: rgba(10, 11, 15, 0.85);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border-left: 1px solid var(--card-border);
            box-shadow: -10px 0 40px rgba(0, 0, 0, 0.5);
            z-index: 101;
            transition: right 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            flex-direction: column;
            padding: 30px;
        }

        .drawer.open {
            right: 0;
        }

        .drawer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }

        .drawer-title {
            font-size: 20px;
            font-weight: 700;
            background: linear-gradient(135deg, #ffffff, #9ca3af);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .drawer-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 20px;
            cursor: pointer;
            transition: var(--transition-smooth);
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .drawer-close:hover {
            background: rgba(255, 255, 255, 0.05);
            color: #ffffff;
        }

        .drawer-content {
            flex-grow: 1;
            overflow-y: auto;
            padding-right: 8px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .drawer-section {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 18px;
        }

        .drawer-section-title {
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
            font-weight: 600;
            margin-bottom: 12px;
        }

        .review-text {
            font-size: 14px;
            line-height: 1.6;
            color: var(--text-primary);
            white-space: pre-wrap;
        }

        /* Empty State */
        .empty-state {
            background: var(--card-bg);
            border: 1px dashed var(--card-border);
            border-radius: 16px;
            padding: 80px 40px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        .empty-icon {
            font-size: 48px;
            color: var(--text-secondary);
            opacity: 0.4;
        }

        .empty-title {
            font-size: 18px;
            font-weight: 600;
            color: #ffffff;
        }

        .empty-desc {
            font-size: 14px;
            color: var(--text-secondary);
            max-width: 320px;
        }

        /* Toast Notifications */
        .toast-container {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .toast {
            background: rgba(10, 11, 15, 0.9);
            border: 1px solid var(--card-border);
            border-left: 4px solid var(--info-color);
            padding: 16px 24px;
            border-radius: 12px;
            backdrop-filter: blur(12px);
            display: flex;
            align-items: center;
            gap: 12px;
            color: #ffffff;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            transform: translateY(100px);
            opacity: 0;
            animation: slideIn 0.35s forwards;
            min-width: 300px;
        }

        .toast.success { border-left-color: var(--success-color); }
        .toast.error { border-left-color: var(--danger-color); }

        @keyframes slideIn {
            to { transform: translateY(0); opacity: 1; }
        }

        .toast-close {
            margin-left: auto;
            cursor: pointer;
            opacity: 0.6;
            transition: var(--transition-smooth);
        }

        .toast-close:hover { opacity: 1; }
    </style>
</head>
<body>

    <header>
        <div class="logo-container">
            <i class="fa-solid fa-brain logo-icon"></i>
            <span class="logo-text">LifeOS AI Dashboard</span>
        </div>
        <div class="status-badge">
            <span class="status-dot"></span>
            <span>Agent Active</span>
        </div>
    </header>

    <main>
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-label">Pending Goal Plans</span>
                <span class="stat-val" id="stat-pending">0</span>
            </div>
            <div class="stat-card">
                <span class="stat-label">Approved today</span>
                <span class="stat-val" id="stat-approved">0</span>
            </div>
            <div class="stat-card">
                <span class="stat-label">Rejected today</span>
                <span class="stat-val" id="stat-rejected">0</span>
            </div>
        </div>

        <div class="section-header">
            <h2 class="section-title">Requires User Confirmation</h2>
            <button class="refresh-btn" id="refresh-btn">
                <i class="fa-solid fa-arrows-rotate"></i>
                <span>Refresh</span>
            </button>
        </div>

        <div class="cards-list" id="cards-list">
            <!-- Loading State -->
            <div style="text-align: center; padding: 40px;" id="loading-spinner">
                <i class="fa-solid fa-spinner fa-spin" style="font-size: 32px; color: var(--text-secondary); opacity: 0.5;"></i>
            </div>
        </div>
    </main>

    <!-- Slide-out Drawer Overlay -->
    <div class="drawer-overlay" id="drawer-overlay"></div>
    
    <!-- Slide-out Drawer -->
    <div class="drawer" id="drawer">
        <div class="drawer-header">
            <h3 class="drawer-title">Goal Planning & Feasibility Review</h3>
            <button class="drawer-close" id="drawer-close">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
        <div class="drawer-content">
            <div class="drawer-section">
                <div class="drawer-section-title">Goal Details Summary</div>
                <div id="drawer-summary" style="display: flex; flex-direction: column; gap: 8px; font-size: 14px;">
                    <!-- Filled dynamically -->
                </div>
            </div>
            <div class="drawer-section">
                <div class="drawer-section-title">Planning & Schedule Insights</div>
                <div class="review-text" id="drawer-review-text">
                    No planning insights attached.
                </div>
            </div>
        </div>
    </div>

    <!-- Toast Notifications Container -->
    <div class="toast-container" id="toast-container"></div>

    <script>
        // State variables
        let pendingExpenses = [];
        let approvedCount = 0;
        let rejectedCount = 0;

        // Element handles
        const cardsList = document.getElementById('cards-list');
        const loadingSpinner = document.getElementById('loading-spinner');
        const refreshBtn = document.getElementById('refresh-btn');
        const drawer = document.getElementById('drawer');
        const drawerOverlay = document.getElementById('drawer-overlay');
        const drawerClose = document.getElementById('drawer-close');
        
        const statPending = document.getElementById('stat-pending');
        const statApproved = document.getElementById('stat-approved');
        const statRejected = document.getElementById('stat-rejected');

        // Fetch data on load
        async function fetchPending() {
            setLoading(true);
            try {
                const response = await fetch('/api/pending');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                pendingExpenses = await response.json();
                renderCards();
                updateStats();
            } catch (error) {
                console.error("Could not fetch pending expenses:", error);
                showToast("Failed to fetch pending approvals.", "error");
                cardsList.innerHTML = `
                    <div class="empty-state">
                        <i class="fa-solid fa-circle-exclamation empty-icon" style="color: var(--danger-color)"></i>
                        <span class="empty-title">Error Loading Expenses</span>
                        <span class="empty-desc">Could not connect to the backend service. Check configuration.</span>
                    </div>
                `;
            } finally {
                setLoading(false);
            }
        }

        function setLoading(isLoading) {
            if (isLoading) {
                loadingSpinner.style.display = 'block';
                if (cardsList.children.length === 1 && cardsList.children[0] === loadingSpinner) {
                    // Do nothing
                } else {
                    cardsList.innerHTML = '';
                    cardsList.appendChild(loadingSpinner);
                }
            } else {
                if (loadingSpinner.parentNode === cardsList) {
                    cardsList.removeChild(loadingSpinner);
                }
            }
        }

        function renderCards() {
            cardsList.innerHTML = '';
            if (pendingExpenses.length === 0) {
                cardsList.innerHTML = `
                    <div class="empty-state">
                        <i class="fa-solid fa-circle-check empty-icon" style="color: var(--success-color)"></i>
                        <span class="empty-title">All Clear!</span>
                        <span class="empty-desc">There are no pending goals requiring confirmation.</span>
                    </div>
                `;
                return;
            }

            pendingExpenses.forEach((exp, idx) => {
                const p = exp.payload || {};
                const amount = parseFloat(p.amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                const date = p.date ? new Date(p.date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : 'No date provided';
                
                const card = document.createElement('div');
                card.className = 'expense-card';
                card.id = `card-${exp.session_id}`;
                card.innerHTML = `
                    <div class="card-header">
                        <div class="submitter-info">
                            <span class="submitter-email">${p.submitter || exp.user_id || 'Unknown Submitter'}</span>
                            <span class="expense-date">${date}</span>
                        </div>
                        <span class="expense-amount">${amount} Days Effort</span>
                    </div>
                    <div class="card-details">
                        <p class="expense-desc">${p.description || 'No description provided.'}</p>
                        <div class="meta-badges">
                            <span class="badge badge-category">
                                <i class="fa-solid fa-tags"></i>
                                <span>${(p.category || 'uncategorized').toUpperCase()}</span>
                            </span>
                            <span class="badge badge-session">
                                <i class="fa-solid fa-hashtag"></i>
                                <span>Session: ${exp.session_id.substring(0, 8)}...</span>
                            </span>
                        </div>
                    </div>
                    <div class="card-actions">
                        <button class="btn btn-view-review" onclick="openReview('${exp.session_id}')">
                            <i class="fa-solid fa-clipboard-check"></i>
                            <span>View Planning Insights</span>
                        </button>
                        <div class="secondary-actions">
                            <button class="btn btn-reject" id="btn-reject-${exp.session_id}" onclick="handleAction('${exp.session_id}', '${exp.interrupt_id}', false)">
                                <span class="spinner"></span>
                                <span class="btn-text">Cancel Plan</span>
                            </button>
                            <button class="btn btn-approve" id="btn-approve-${exp.session_id}" onclick="handleAction('${exp.session_id}', '${exp.interrupt_id}', true)">
                                <span class="spinner"></span>
                                <span class="btn-text">Activate Plan</span>
                            </button>
                        </div>
                    </div>
                `;
                cardsList.appendChild(card);
            });
        }

        async function handleAction(sessionId, interruptId, approved) {
            const btnApprove = document.getElementById(`btn-approve-${sessionId}`);
            const btnReject = document.getElementById(`btn-reject-${sessionId}`);
            const activeBtn = approved ? btnApprove : btnReject;
            const otherBtn = approved ? btnReject : btnApprove;
            
            activeBtn.classList.add('loading');
            activeBtn.disabled = true;
            otherBtn.disabled = true;

            try {
                const response = await fetch(`/api/action/${sessionId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        interrupt_id: interruptId,
                        approved: approved
                    })
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.detail || "Server error");
                }

                // Smooth fade-out of the card
                const card = document.getElementById(`card-${sessionId}`);
                card.style.transition = 'all 0.5s ease';
                card.style.opacity = '0';
                card.style.transform = 'scale(0.9) translateY(20px)';
                
                setTimeout(() => {
                    pendingExpenses = pendingExpenses.filter(e => e.session_id !== sessionId);
                    renderCards();
                    
                    if (approved) {
                        approvedCount++;
                    } else {
                        rejectedCount++;
                    }
                    updateStats();
                }, 500);

                showToast(`Goal plan successfully ${approved ? 'activated' : 'cancelled'}.`, "success");

            } catch (error) {
                console.error("Action error:", error);
                showToast(`Failed to process action: ${error.message}`, "error");
                activeBtn.classList.remove('loading');
                activeBtn.disabled = false;
                otherBtn.disabled = false;
            }
        }

        function openReview(sessionId) {
            const exp = pendingExpenses.find(e => e.session_id === sessionId);
            if (!exp) return;

            const p = exp.payload || {};
            const amount = parseFloat(p.amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            
            document.getElementById('drawer-summary').innerHTML = `
                <div style="display:flex; justify-content:space-between;"><strong>Submitter:</strong> <span>${p.submitter || 'N/A'}</span></div>
                <div style="display:flex; justify-content:space-between;"><strong>Effort:</strong> <span style="font-weight:600;">${amount} Days</span></div>
                <div style="display:flex; justify-content:space-between;"><strong>Category:</strong> <span>${p.category || 'N/A'}</span></div>
                <div style="display:flex; justify-content:space-between;"><strong>Description:</strong> <span>${p.description || 'N/A'}</span></div>
            `;

            const reviewText = exp.review || "No scheduling conflicts or risk factors flagged. Ready for activation.";
            document.getElementById('drawer-review-text').innerText = reviewText;

            drawer.classList.add('open');
            drawerOverlay.classList.add('open');
        }

        function closeDrawer() {
            drawer.classList.remove('open');
            drawerOverlay.classList.remove('open');
        }

        function updateStats() {
            statPending.innerText = pendingExpenses.length;
            statApproved.innerText = approvedCount;
            statRejected.innerText = rejectedCount;
        }

        function showToast(message, type = "info") {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            
            let icon = 'fa-circle-info';
            if (type === 'success') icon = 'fa-circle-check';
            if (type === 'error') icon = 'fa-circle-exclamation';

            toast.innerHTML = `
                <i class="fa-solid ${icon}"></i>
                <span>${message}</span>
                <i class="fa-solid fa-xmark toast-close" onclick="this.parentNode.remove()"></i>
            `;
            container.appendChild(toast);

            setTimeout(() => {
                toast.style.transition = 'all 0.5s ease';
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-20px)';
                setTimeout(() => toast.remove(), 500);
            }, 4000);
        }

        // Event listeners
        refreshBtn.addEventListener('click', fetchPending);
        drawerClose.addEventListener('click', closeDrawer);
        drawerOverlay.addEventListener('click', closeDrawer);

        // Initial Load
        fetchPending();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the polished LifeOS AI dashboard HTML page."""
    return HTMLResponse(content=HTML_CONTENT)

@app.get("/api/pending")
async def get_pending():
    """Queries the ADK VertexAiSessionService to find pending approvals.
    
    Lists all sessions, fetches the full history for each session, and identifies
    unresolved adk_request_input function call events (where a function call
    has no matching function response event by ID).
    """
    try:
        session_service = get_session_service()
        list_resp = await session_service.list_sessions(app_name="expense_agent")
        sessions = list_resp.sessions or []
        
        pending_list = []
        
        for session in sessions:
            try:
                full_session = await session_service.get_session(
                    app_name="expense_agent",
                    user_id=session.user_id,
                    session_id=session.id
                )
                if not full_session:
                    continue
                
                calls = {}
                responses = set()
                review_summary = None
                
                for event in full_session.events:
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            fc = part.function_call
                            if fc:
                                if fc.name == "adk_request_input":
                                    args = fc.args or {}
                                    payload = args.get("payload") or {}
                                    if isinstance(payload, str):
                                        try:
                                            payload = json.loads(payload)
                                        except Exception:
                                            pass
                                    calls[fc.id] = {
                                        "session_id": full_session.id,
                                        "interrupt_id": fc.id,
                                        "message": args.get("message", ""),
                                        "payload": payload,
                                        "user_id": full_session.user_id
                                    }
                                elif fc.name == "emit_expense_alert":
                                    args = fc.args or {}
                                    if args.get("risk_summary"):
                                        review_summary = args["risk_summary"]
                                        
                            fr = part.function_response
                            if fr and fr.name == "adk_request_input":
                                responses.add(fr.id)
                
                for cid, call_info in calls.items():
                    if cid not in responses:
                        if review_summary:
                            call_info["review"] = review_summary
                        pending_list.append(call_info)
                        
            except Exception as se:
                logger.error(f"Error fetching/processing session {session.id}: {se}")
                continue
                
        return pending_list
        
    except Exception as e:
        logger.error(f"Error listing pending sessions: {e}")
        return []

@app.post("/api/action/{session_id}")
async def handle_action(session_id: str, request: Request):
    """Resumes the paused session on Agent Runtime.
    
    Translates the approved status decision back into the agent workflow.
    To avoid duplicate parameter errors on the ADK runner, the resume payload
    is passed directly as the message argument.
    """
    try:
        body = await request.json()
        interrupt_id = body.get("interrupt_id")
        approved = body.get("approved")
        
        if approved is None or not interrupt_id:
            raise HTTPException(status_code=400, detail="Missing approved status or interrupt_id.")
            
        proj = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT") or os.environ.get("PROJECT_ID")
        runtime_id = os.environ.get("AGENT_RUNTIME_ID")
        loc = os.environ.get("GCP_REGION") or os.environ.get("LOCATION") or os.environ.get("GOOGLE_CLOUD_LOCATION", "us-east1")
        
        if not proj or not runtime_id:
            raise HTTPException(
                status_code=500, 
                detail="GCP_PROJECT/PROJECT_ID and AGENT_RUNTIME_ID environment variables must be configured."
            )
            
        # Initialize Vertex AI SDK
        vertexai.init(project=proj, location=loc)
        
        # Load reasoning engine
        re = ReasoningEngine(runtime_id)
        
        # Construct the resume payload as specified
        resume_payload = {
            "role": "user",
            "parts": [
                {
                    "function_response": {
                        "id": interrupt_id,
                        "name": "adk_request_input",
                        "response": {
                            "approved": approved
                        }
                    }
                }
            ]
        }
        
        # Query reasoning engine with user_id strictly set to "default-user"
        logger.info(f"Resuming session {session_id} on ReasoningEngine {runtime_id} with approved={approved}")
        response = re.query(
            message=resume_payload,
            user_id="default-user",
            session_id=session_id
        )
        
        return {"status": "success", "response": response}
        
    except Exception as e:
        logger.error(f"Error resuming session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume session: {str(e)}"
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
