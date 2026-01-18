"""
Constants for Experiment Wizard.

Shared configuration for page mapping and metrics definitions.
"""

# Page and Component Mapping for Target App
PAGE_MAP = {
    "메인 홈 (/)": {
        "url": "/",
        "components": {
            "메인 배너 (Hero Banner)": {"id": "hero-banner", "type": "BANNER"},
            "카테고리 아이콘 (Category Icons)": {"id": "category-nav", "type": "ICON_SET"}
        }
    },
    "상세 페이지 (/detail)": {
        "url": "/detail",
        "components": {
            "구매하기 버튼 (Primary CTA)": {"id": "add-to-cart-btn", "type": "BUTTON"},
            "상품 가격 (Price Label)": {"id": "price-tag", "type": "TEXT"}
        }
    },
    "장바구니 (/cart)": {
        "url": "/cart",
        "components": {
            "주문 결제 버튼 (Checkout CTA)": {"id": "checkout-btn", "type": "BUTTON"}
        }
    },
    "검색 결과 (/search)": {
        "url": "/search",
        "components": {
            "검색 결과 카드 (Result Item)": {"id": "search-result-item", "type": "LAYOUT"}
        }
    },
    "주문 배달 현황 (/tracking)": {
        "url": "/tracking",
        "components": {
            "도착 예정 시간 (ETA Header)": {"id": "arrival-time", "type": "TEXT"},
            "라이더 마커 (Driver Icon)": {"id": "driver-marker", "type": "ICON"}
        }
    }
}

# Metrics database for A/B testing
METRICS_DB = {
    "CTR (클릭률)": {
        "desc": "노출 대비 클릭한 비율",
        "formula": "Clicks / Impressions",
        "type": "Conversion"
    },
    "CVR (전환율)": {
        "desc": "방문자 중 실제 구매 비율",
        "formula": "Orders / Visitors",
        "type": "Conversion"
    },
    "AOV (평균 주문액)": {
        "desc": "구매 고객 1인당 평균 결제 금액",
        "formula": "Revenue / Orders",
        "type": "Revenue"
    },
    "Bounce Rate (이탈률)": {
        "desc": "첫 페이지만 보고 나가는 비율",
        "formula": "One-page / Total",
        "type": "Retention"
    },
}

# Default values
DEFAULT_SPLIT_RATIO = 0.5
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.8
DEFAULT_MDE = 0.10
