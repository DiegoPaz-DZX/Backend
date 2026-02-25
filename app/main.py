import csv
import io
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from .schemas import envioInfo, envioUsers, editarUser, LoginRequest, Cambiarcontra
from .database import get_db
from . import models
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import resend

router = APIRouter()

@router.get("/tablas")
async def obtener_data(db: Session = Depends(get_db)):
    try:
        gastos = db.query(models.Gasto).order_by(models.Gasto.id.asc()).all()
        return gastos
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        raise HTTPException(status_code=400, detail="Error en la base de datos.")

@router.post("/rellenarTabla")
async def enviar_data(info: envioInfo, db: Session = Depends(get_db)):
    try:
        nuevo_gasto = models.Gasto(
            date=info.date,
            mount=info.mount,
            category=info.category,
            description=info.description
        )
        db.add(nuevo_gasto)
        db.commit()
        db.refresh(nuevo_gasto)
        return {"message": "Gasto agregado", "data": nuevo_gasto}
    except Exception as e:
        db.rollback()
        print(f"Error al insertar: {e}")
        raise HTTPException(status_code=400, detail="Error al rellenar la tabla.")
    
@router.get("/usersTablas")
async def obtener_usuarios(db: Session = Depends(get_db)):
    try:
        usuarios = db.query(models.Usuario).order_by(models.Usuario.id.asc()).all()
        return usuarios
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        raise HTTPException(status_code=400, detail="Error en la base de datos.")
    
@router.delete("/eliminarGasto/{gasto_id}")
async def eliminar_gasto(gasto_id: int, db: Session = Depends(get_db)):
    try:
        gasto = db.query(models.Gasto).filter(models.Gasto.id == gasto_id).first()
        if not gasto:
            raise HTTPException(status_code=404, detail="El registro no existe en la base de datos.")
        db.delete(gasto)
        db.commit()
        return {"message": "Gasto eliminado correctamente", "id": gasto_id}
    except Exception as e:
        db.rollback()
        print(f"Error al eliminar: {e}")
        raise HTTPException(status_code=400, detail="No se pudo eliminar el gasto.")


@router.post("/login")
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(
        models.Usuario.email == data.email,
        models.Usuario.password == data.password
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    return {
        "message": "Login correcto",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    }

@router.get("/gastosXfecha")
async def obtener_data(db: Session = Depends(get_db)):
    try:
        gastos = db.query(models.Gasto).order_by(models.Gasto.date.asc()).all()
        return gastos
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        raise HTTPException(status_code=400, detail="Error en la base de datos.")
    
    
@router.patch("/cambiarContraseña")
async def cambiar_contraseña(data : Cambiarcontra,  db: Session = Depends(get_db) ):
    usuario = db.query(models.Usuario).filter(models.Usuario.email==data.email).first()
    
    if not usuario:
        raise HTTPException(status_code=400, detail="Correo no encontrado")
    
    if data.nueva != data.confirmar:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")
    
    usuario.password = data.nueva
    db.commit()
    db.refresh(usuario)
    return{
        "message" : "Contraseña actualizada correctamente"
    }
    
    codes_db = {}

@router.post("/enviarCodigoRecuperacion")
async def enviar_codigo(email: str, db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="El correo no existe")
    codigo = str(random.randint(100000, 999999))
    codes_db[email] = codigo

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {resend.api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": "Soporte <onboarding@resend.dev>", #CAMBIAR AL TENER DOMINIO
        "to": [email],
        "subject": f"{codigo} es tu código de recuperación",
        "html": f"""
            <div style="background-color:#141414; color:white; padding:30px; border-radius:15px; font-family:sans-serif;">
                <h2 style="color:#10b981;">Recuperación de Cuenta</h2>
                <p>Tu código de seguridad es:</p>
                <h1 style="letter-spacing:10px; font-size:40px; color:white;">{codigo}</h1>
                <p>Si no solicitaste este cambio, ignora este correo.</p>
            </div>
        """
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, headers=headers, json=payload)

    return {"message": "Código enviado correctamente"}

@router.post("/verificarCodigo")
async def verificar_codigo(email: str, codigo: str):
    if email in codes_db and codes_db[email] == codigo:
        return {"message": "Código válido"}
    raise HTTPException(status_code=400, detail="Código incorrecto o expirado")
    
@router.patch("/editTableGastos/{gasto_id}")
async def cambiar_data(gasto_id: int, info: envioInfo, db: Session = Depends(get_db)):
    try:
            gasto_existente = db.query(models.Gasto).filter(models.Gasto.id == gasto_id).first()
            if not gasto_existente:
                HTTPException(status_code=400, detail="El gasto no existe.")

            gasto_existente.date = info.date
            gasto_existente.mount = info.mount
            gasto_existente.category = info.category
            gasto_existente.description = info.description
            db.commit()
            db.refresh(gasto_existente)
            return {"message": "Gasto modificado", "data": gasto_existente}
    except Exception as e:
            db.rollback()
            print(f"Error al modificar: {e}")
            raise HTTPException(status_code=400, detail="Error al modificar algo en la tabla.")
        
@router.post("/rellenarUsers")
async def enviar_data(info: envioUsers, db: Session = Depends(get_db)):
    try:
        nuevo_user = models.Usuario(
            username=info.username,
            email=info.email,
            password=info.password
        )
        db.add(nuevo_user)
        db.commit()
        db.refresh(nuevo_user)
        return {"message": "Nuevo usuario agregado", "data": nuevo_user}
    except Exception as e:
        db.rollback()
        print(f"--- ERROR DE BASE DE DATOS: {str(e)} ---")
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo crear el usuario: {str(e)}"
        )

#Probar para gestión de usuarios
@router.get("/usuariosRol/{rol}")
async def obtener_usuarios_por_rol(rol: str, db: Session = Depends(get_db)):
    try:
        usuarios = db.query(models.Usuario).filter(models.Usuario.userrole == rol).all()
        return usuarios
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al filtrar")

resend.api_key = "re_VBVEiuND_HAg9HQgSdCStWUyiqf5uY6Pv"

@router.post("/register")
async def register_user(info: envioUsers, db: Session = Depends(get_db)):
    try:
        nuevo_user = models.Usuario(
            username=info.username,
            email=info.email,
            password=info.password,
            emailverified=False
        )
        db.add(nuevo_user)
        db.commit()
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {resend.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": "Acme <onboarding@resend.dev>",
            "to": [info.email],
            "subject": "Confirma tu cuenta",
            "html": f"<strong>Hola {info.username}</strong>, haz clic <a href='http://127.0.0.1:8000/verify/{info.email}'>aquí</a> para                 activar tu cuenta."
        }
        async with httpx.AsyncClient() as client:
            await client.post(url, headers=headers, json=payload)
        return {"message": "Registro exitoso, revisa tu correo."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

#EXPOTAR PDF Y CSV
@router.get("/exportar/csv")
async def exportar_csv(db: Session = Depends(get_db)):
    try:
        gastos = db.query(models.Gasto).order_by(models.Gasto.id.asc()).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Fecha", "Monto", "Categoría", "Descripción"])
        for g in gastos:
            writer.writerow([g.id, g.date, g.mount, g.category, g.description])
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=reporte_egresos.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/exportar/pdf")
async def exportar_pdf(db: Session = Depends(get_db)):
    try:
        gastos = db.query(models.Gasto).order_by(models.Gasto.id.asc()).all()
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, "Reporte de Egresos Registrados")

        p.setFont("Helvetica", 10)
        y = 700
        for g in gastos:
            linea = f"ID: {g.id} | Fecha: {g.date} | Monto: S/. {g.mount} | Categoría: {g.category}"
            p.drawString(100, y, linea)
            y -= 20
            if y < 50:
                p.showPage()
                y = 750
        p.save()
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=reporte_egresos.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#NOTIFICACION

@router.post("/configurarPresupuesto")
async def set_presupuesto(info: PresupuestoSchema, db: Session = Depends(get_db)):
    try:
        existente = db.query(models.Presupuesto).filter(
            models.Presupuesto.month_year == info.month_year
        ).first()
        if existente:
            existente.limit_mount = info.limit_mount
            existente.category = info.category
        else:
            nuevo = models.Presupuesto(**info.model_dump())
            db.add(nuevo)
        db.commit()
        return {"message": "Presupuesto actualizado con éxito"}
    except Exception as e:
        db.rollback()
        print(f"Error detectado: {e}")
        raise HTTPException(status_code=400, detail=f"Error en la base de datos: {str(e)}")

@router.get("/alertasPresupuesto")
async def obtener_alertas(db: Session = Depends(get_db)):
    total_gastado = db.query(func.sum(models.Gasto.mount)).scalar() or 0
    presupuesto = db.query(models.Presupuesto).order_by(models.Presupuesto.id.desc()).first()
    if not presupuesto:
        return []
    alertas = []
    porcentaje = (total_gastado / presupuesto.limit_mount) * 100
    if porcentaje >= 100:
        alertas.append("¡CUIDADO! Has superado el presupuesto establecido.")
    elif porcentaje >= 80:
        alertas.append("Atención: Tus egresos están cerca de exceder tu presupuesto (80%+).")
    return alertas

@router.get("/obtenerPresupuestoActual")
async def obtener_presupuesto(db: Session = Depends(get_db)):
    presupuesto = db.query(models.Presupuesto).order_by(models.Presupuesto.id.desc()).first()
    if not presupuesto:
        return {"limit_mount": 2000, "month_year": "2026-02", "category": "TOTAL"}
    return presupuesto

@router.patch("/editTableUsers/{usuario_id}")
async def cambiar_usuario(usuario_id: int, info: editarUser, db: Session = Depends(get_db)):
    try:
        usuario_existente = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
        if not usuario_existente:
            HTTPException(status_code=400, detail="El usuario no existe.")

        usuario_existente.username = info.username
        usuario_existente.email = info.email
        db.commit()
        db.refresh(usuario_existente)
        return {"message": "Usuario modificado", "data": usuario_existente}
    except Exception as e:
        db.rollback()
        print(f"Error al editar el Usuario: {e}")
        raise HTTPException(status_code=400, detail="Error al modificar el usuario en la tabla.")

#Probar para gestionEgresos    
@router.get("/gastosPorCategoria/{categoria}")
async def obtener_gastos_categoria(categoria: str, db: Session = Depends(get_db)):
    try:
        gastos = db.query(models.Gasto).filter(models.Gasto.category == categoria).order_by(models.Gasto.date.asc()).all()
        
        if not gastos:
            raise HTTPException(status_code=404, detail=f"No hay egresos en la categoría: {categoria}")
            
        return gastos
    except Exception as e:
        print(f"Error al filtrar egresos: {e}")
        raise HTTPException(status_code=500, detail="Error en la base de datos.")