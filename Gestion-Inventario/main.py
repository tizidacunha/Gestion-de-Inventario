from fastapi import FastAPI, HTTPException
import cx_Oracle
from models import Inventario

app = FastAPI()

cx_Oracle.init_oracle_client(lib_dir=r"C:\instantclient_19_20")
conn = cx_Oracle.connect('rosi_efis/rosi_efis@10.30.205.127:1521/fisco')

@app.post("/agregar_producto")
def agregar_producto(dato: Inventario):
    cursor = conn.cursor()
    #verificar si ya existe el producot
    try:
        cursor.execute("SELECT * FROM inventario WHERE nombre = :nombre", {'nombre': dato.nombre})
        existe = cursor.fetchone()
        if existe: #si existe sumarle la cantidad nueva
            nueva_cantidad = existe[2] + dato.cantidad
            cursor.execute("UPDATE inventario SET cantidad = :cantidad WHERE id = :id", {'cantidad': nueva_cantidad, 'id': existe[0]})
        else: #si no existe crear nuevo
            cursor.execute("INSERT INTO inventario (id, nombre, cantidad, precio) VALUES (inventario_sequ.nextval, :nombre, :cantidad, :precio)",
                           {'nombre': dato.nombre, 'cantidad': dato.cantidad, 'precio': dato.precio})
        conn.commit()
        return {"mensaje": "Producto agregado o actualizado exitosamente"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al agregar o actualizar producto: {str(e)}")
    finally:
        cursor.close()


# agregar esto en base de datos
# CREATE SEQUENCE inventario_seq
#   START WITH 1
#   INCREMENT BY 1
#   NOCACHE;



@app.get("/obtener_inventario")
def obtener_inventario():
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM inventario")
        productos = []
        for row in cursor.fetchall():
            productos.append({"id": row[0], "nombre": row[1], "cantidad": row[2], "precio": row[3]})
        return productos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener inventario: {str(e)}")
    finally:
        cursor.close()


@app.delete("/delete")
def delete_dato(id: int):
    try:
        con = cx_Oracle.connect('rosi_efis/rosi_efis@10.30.205.127:1521/fisco')
        cur = con.cursor()
        cur.execute('DELETE FROM inventario WHERE id = :id', {'id': id})
        con.commit()
    
    
    except Exception as err:
        error = f"{err}"
        print(f"ERROR: {error}")
        return error #JSONResponse(json.dumps(err),500)
    finally:
        con.close() 

@app.get("/obtener-stock")
def obtener_stock(nombre_producto: str):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT cantidad FROM inventario WHERE nombre = :nombre", {'nombre': nombre_producto})
        cantidad_stock = cursor.fetchone()
        if cantidad_stock :
            return {"nombre": nombre_producto, "cantidad_stock": cantidad_stock[0]}
        else:
            raise HTTPException(status_code=404, detail=f"Producto '{nombre_producto}' no encontrado en el inventario, agregar stock")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener cantidad de stock: {str(e)}")
    finally:
        cursor.close()



@app.put("/modificar_stock/{nombre_producto}")
def modificar_stock(nombre_producto: str, cantidad_a_restar: int):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT cantidad FROM inventario WHERE nombre = :nombre", {'nombre': nombre_producto})
        cantidad_stock = cursor.fetchone() #devuelve la primera fila
        if cantidad_stock:
            cantidad_actual = cantidad_stock[0] #asigna el valor de cantidad stock a cantidad actual
            if cantidad_actual >= cantidad_a_restar: #pregunta si cantidad actual es mayor e igual que la que vas a restar
                nueva_cantidad = cantidad_actual - cantidad_a_restar #asigna el valor de la nueva cantidad
                cursor.execute("UPDATE inventario SET cantidad = :cantidad WHERE nombre = :nombre",
                               {'cantidad': nueva_cantidad, 'nombre': nombre_producto})
                conn.commit()
                return {"mensaje": f"Se han restado {cantidad_a_restar} unidades del producto '{nombre_producto}'. Nuevo stock: {nueva_cantidad}"}
            else: #si la cantidad a restar es mayor que la actual no se puede
                raise HTTPException(status_code=400, detail=f"No hay suficiente stock del producto '{nombre_producto}' para restar {cantidad_a_restar} unidades.")
        else:
            raise HTTPException(status_code=404, detail=f"Producto '{nombre_producto}' no encontrado en el inventario.")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al modificar el stock del producto: {str(e)}, (no existe)")
    finally:
        cursor.close()


