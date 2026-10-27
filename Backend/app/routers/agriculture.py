"""
Module 3: Shops, products, stock, and farmer product requests.
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user

router = APIRouter(prefix="/agriculture", tags=["agriculture"])


def _product_out(product: models.Product) -> schemas.ProductOut:
    out = schemas.ProductOut.model_validate(product)
    out.is_low_stock = product.stock <= (product.low_stock_threshold or 5)
    return out


@router.post("/shops", response_model=schemas.ShopOut)
def create_shop(
    shop_in: schemas.ShopCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing = db.query(models.Shop).filter(models.Shop.owner_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have a shop")

    shop = models.Shop(owner_id=current_user.id, **shop_in.model_dump())
    db.add(shop)
    db.commit()
    db.refresh(shop)
    return shop


@router.get("/shops", response_model=List[schemas.ShopOut])
def list_shops(db: Session = Depends(get_db)):
    return db.query(models.Shop).all()


@router.patch("/shops/mine", response_model=schemas.ShopOut)
def update_my_shop(
    update_in: schemas.ShopUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    shop = db.query(models.Shop).filter(models.Shop.owner_id == current_user.id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="You don't have a shop yet")

    for field, value in update_in.model_dump(exclude_unset=True).items():
        setattr(shop, field, value)

    db.commit()
    db.refresh(shop)
    return shop


@router.post("/shops/{shop_id}/products", response_model=schemas.ProductOut)
def add_product(
    shop_id: int,
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    if shop.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your shop")

    product = models.Product(shop_id=shop_id, **product_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return _product_out(product)


@router.get("/products", response_model=List[schemas.ProductOut])
def list_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return [_product_out(p) for p in products]


@router.patch("/products/{product_id}", response_model=schemas.ProductOut)
def update_product(
    product_id: int,
    update_in: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    shop = db.query(models.Shop).filter(models.Shop.id == product.shop_id).first()
    if shop.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your product")

    for field, value in update_in.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return _product_out(product)


@router.get("/shops/mine/low-stock", response_model=List[schemas.ProductOut])
def my_low_stock_products(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    shop = db.query(models.Shop).filter(models.Shop.owner_id == current_user.id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="You don't have a shop yet")

    products = db.query(models.Product).filter(models.Product.shop_id == shop.id).all()
    low = [_product_out(p) for p in products]
    return [p for p in low if p.is_low_stock]


@router.post("/requests", response_model=schemas.ProductRequestOut)
def create_product_request(
    request_in: schemas.ProductRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = db.query(models.Product).filter(models.Product.id == request_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < request_in.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    req = models.ProductRequest(
        product_id=request_in.product_id,
        farmer_id=current_user.id,
        quantity=request_in.quantity,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.post("/requests/batch", response_model=List[schemas.ProductRequestOut])
def create_batch_product_request(
    batch_in: schemas.BatchProductRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not batch_in.items:
        raise HTTPException(status_code=400, detail="No items in request")

    # Validate every item BEFORE creating anything, so a batch either
    # succeeds completely or fails completely — no half-created orders.
    products = {}
    for item in batch_in.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for '{product.name}'")
        products[item.product_id] = product

    batch_id = uuid.uuid4().hex
    created = []
    for item in batch_in.items:
        req = models.ProductRequest(
            product_id=item.product_id,
            farmer_id=current_user.id,
            quantity=item.quantity,
            batch_id=batch_id,
        )
        db.add(req)
        created.append(req)

    db.commit()
    for req in created:
        db.refresh(req)
    return created


@router.get("/requests/mine", response_model=List[schemas.ProductRequestOut])
def my_product_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.ProductRequest)
        .filter(models.ProductRequest.farmer_id == current_user.id)
        .order_by(models.ProductRequest.created_at.desc())
        .all()
    )


@router.get("/shops/mine/requests", response_model=List[schemas.ProductRequestOut])
def incoming_requests_for_my_shop(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    shop = db.query(models.Shop).filter(models.Shop.owner_id == current_user.id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="You don't have a shop yet")

    return (
        db.query(models.ProductRequest)
        .join(models.Product)
        .filter(models.Product.shop_id == shop.id)
        .order_by(models.ProductRequest.created_at.desc())
        .all()
    )


@router.patch("/requests/{request_id}/status", response_model=schemas.ProductRequestOut)
def update_product_request_status(
    request_id: int,
    status_in: schemas.ProductRequestStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    req = db.query(models.ProductRequest).filter(models.ProductRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    product = db.query(models.Product).filter(models.Product.id == req.product_id).first()
    shop = db.query(models.Shop).filter(models.Shop.id == product.shop_id).first()
    if shop.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your shop's request")

    if status_in.status == models.ProductRequestStatus.approved and req.status != models.ProductRequestStatus.approved:
        if product.stock < req.quantity:
            raise HTTPException(status_code=400, detail="Not enough stock to approve this request")
        product.stock -= req.quantity

    req.status = status_in.status
    db.commit()
    db.refresh(req)
    return req
