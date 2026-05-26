from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Continente(Base):
    __tablename__ = 'continentes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False)
    
    # Relaciones
    paises = relationship("Pais", back_populates="continente")

    def __repr__(self):
        return f"<Continente(nombre='{self.nombre}')>"


class Pais(Base):
    __tablename__ = 'paises'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False)
    continente_id = Column(Integer, ForeignKey('continentes.id'), nullable=False)
    
    # Relaciones
    continente = relationship("Continente", back_populates="paises")
    
    # Para resolver la ambigüedad de múltiples claves foráneas apuntando a la misma tabla,
    # especificamos foreign_keys en la relación o como string.
    jugadores_nacimiento = relationship(
        "Jugador", 
        foreign_keys="[Jugador.pais_nacimiento_id]", 
        back_populates="pais_nacimiento"
    )
    jugadores_donde_juega = relationship(
        "Jugador", 
        foreign_keys="[Jugador.pais_donde_juega_id]", 
        back_populates="pais_donde_juega"
    )

    def __repr__(self):
        return f"<Pais(nombre='{self.nombre}')>"


class Jugador(Base):
    __tablename__ = 'jugadores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False)
    pais_nacimiento_id = Column(Integer, ForeignKey('paises.id'), nullable=False)
    pais_donde_juega_id = Column(Integer, ForeignKey('paises.id'), nullable=False)
    posicion = Column(String(100))
    edad = Column(Integer)
    numero_partidos_seleccion = Column(Integer)
    goles_seleccion = Column(Integer)
    
    # Relaciones
    pais_nacimiento = relationship(
        "Pais", 
        foreign_keys=[pais_nacimiento_id], 
        back_populates="jugadores_nacimiento"
    )
    pais_donde_juega = relationship(
        "Pais", 
        foreign_keys=[pais_donde_juega_id], 
        back_populates="jugadores_donde_juega"
    )

    def __repr__(self):
        return f"<Jugador(nombre='{self.nombre}', posicion='{self.posicion}')>"
