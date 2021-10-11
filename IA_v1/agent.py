import math, sys
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from random import randrange

DIRECTIONS = Constants.DIRECTIONS
game_state = None
#ROAD MAP
''' 
V2
GESTION CART
GESTION RESSOURCE
RECOLTE OPTIMISE
V3
JOBS ?
ROADS
PILLAGE
TRANSFER
OUTPOST/MAIN CITY(CART)
    '''    


def getresourceTiles():
    resourceTiles: list[Cell] = []
    for y in range(game_state.map.height):
        for x in range(game_state.map.width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resourceTiles.append(cell)
    return resourceTiles

def getCityTiles(player):
    cityTiles: list[Cell] = []
    for city in player.cities.values():
        for cityTile in city.citytiles:
            cityTiles.append(cityTile)
    return cityTiles

def getBestMove(unitPos, destinationPos, nextMoves, player, avoidCity):
    # E:x+1, W:x-1, N:y-1, S:y+1
    # Get best move
    bestDir = unitPos.direction_to(destinationPos)
    bestNextCell = game_state.map.get_cell_by_pos(unitPos.translate(bestDir,1))
    unitPositions = []
    for otherUnit in player.units:
        if otherUnit.pos != unitPos and not otherUnit.can_act() and game_state.map.get_cell_by_pos(otherUnit.pos).citytile is None:
            unitPositions.append(otherUnit.pos)    
    if bestNextCell.pos not in unitPositions and bestNextCell.pos not in nextMoves:
        if avoidCity:
            if bestNextCell.citytile is None:
                return bestDir
        else:
            return bestDir
    # Get alternative move
    alternativeDIrection = {}
    if bestDir == Constants.DIRECTIONS.NORTH or bestDir == Constants.DIRECTIONS.SOUTH:
        if unitPos.x > 0:
            nextCell: Cell = game_state.map.get_cell_by_pos(unitPos.translate(Constants.DIRECTIONS.WEST, 1))
            if nextCell.pos not in unitPositions and nextCell.pos not in nextMoves:
                if avoidCity:
                    if nextCell.citytile is None:
                        alternativeDIrection[Constants.DIRECTIONS.WEST] = nextCell.pos.distance_to(destinationPos)
                else:
                    alternativeDIrection[Constants.DIRECTIONS.WEST] = nextCell.pos.distance_to(destinationPos)
        if unitPos.x < game_state.map.width-1:
            nextCell: Cell = game_state.map.get_cell_by_pos(unitPos.translate(Constants.DIRECTIONS.EAST, 1))
            if nextCell.pos not in unitPositions and nextCell.pos not in nextMoves:
                if avoidCity:
                    if nextCell.citytile is None:
                        alternativeDIrection[Constants.DIRECTIONS.EAST] = nextCell.pos.distance_to(destinationPos)
                else:
                    alternativeDIrection[Constants.DIRECTIONS.EAST] = nextCell.pos.distance_to(destinationPos)
    else :
        if unitPos.y > 0:
            nextCell: Cell = game_state.map.get_cell_by_pos(unitPos.translate(Constants.DIRECTIONS.NORTH, 1))
            if nextCell.pos not in unitPositions and nextCell.pos not in nextMoves:
                if avoidCity:
                    if nextCell.citytile is None:
                        alternativeDIrection[Constants.DIRECTIONS.NORTH] = nextCell.pos.distance_to(destinationPos)
                else:
                    alternativeDIrection[Constants.DIRECTIONS.NORTH] = nextCell.pos.distance_to(destinationPos)
        if unitPos.y < game_state.map.height-1:
            nextCell: Cell = game_state.map.get_cell_by_pos(unitPos.translate(Constants.DIRECTIONS.SOUTH, 1))
            if nextCell.pos not in unitPositions and nextCell.pos not in nextMoves:
                if avoidCity:
                    if nextCell.citytile is None:
                        alternativeDIrection[Constants.DIRECTIONS.SOUTH] = nextCell.pos.distance_to(destinationPos)
                else:
                    alternativeDIrection[Constants.DIRECTIONS.SOUTH] = nextCell.pos.distance_to(destinationPos)
    if len(alternativeDIrection) == 0:
        newDir = Constants.DIRECTIONS.CENTER
    else:
        newDir = min(alternativeDIrection, key=alternativeDIrection.get)
    return newDir


def getClosestCityTile(unit, player):
    closestCityTile: Cell = None
    ctClosestDist = math.inf
    for ct in getCityTiles(player):
        dist = ct.pos.distance_to(unit.pos)
        if dist < ctClosestDist:
            ctClosestDist = dist
            closestCityTile = ct
    return closestCityTile

def getAdjCells(x,y):
    adjCells: list[Cell] = []
    if x < game_state.map.width-1:
        adjCells.append(game_state.map.get_cell(x+1, y))
    if x > 0:
        adjCells.append(game_state.map.get_cell(x-1, y))
    if y < game_state.map.height-1:    
        adjCells.append(game_state.map.get_cell(x, y+1))
    if y > 0:
        adjCells.append(game_state.map.get_cell(x, y-1))
    return adjCells

def getCell(unit):
    cell: Cell = None
    cell = game_state.map.get_cell_by_pos(unit.pos)
    return  cell

def getConstructionSites(player):
    constructionSite: list[Cell] = []
    cityTiles = getCityTiles(player)
    for ct in cityTiles:
        for adjCell in getAdjCells(ct.pos.x, ct.pos.y):
            if adjCell.citytile is None and not adjCell.has_resource():
                constructionSite.append(adjCell)
    # If there is no contruction site available pick the closest cell
    if len(constructionSite) == 0:
        closestTile = None
        closestDist = math.inf
        for y in range(game_state.map.height):
            for x in range(game_state.map.width):
                cell: Cell = game_state.map.get_cell(x, y)
                if cell.citytile is None and not cell.has_resource():
                    dist = cityTiles[0].pos.distance_to(cell.pos)
                    print(dist)
                    if dist < closestDist:
                        closestTile = cell
                        closestDist = dist
        constructionSite.append(closestTile)
                
    return constructionSite

def ImReadyForTheNight(player):
    ready = True
    for city in player.cities.values():
        if city.fuel < (city.get_light_upkeep() * 10) + 50 :
            ready = False
    return ready


def agent(observation, configuration):
    global game_state
    

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])
    
    actions = []

    ### AI Code goes down here! ### 
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height
    resourceTiles = getresourceTiles()
    cityTiles = getCityTiles(player)
    nextMoves = []
    building = False
    nbUnit = len(player.units)
    


########################################################################################################################
    # CITIES
    # we iterate over all our city tiles and do something with them
    for cityTile in cityTiles:
        if cityTile.can_act():
            # For each city tiles
            if nbUnit < len(cityTiles):
                actions.append(cityTile.build_worker())
                nbUnit += 1
                '''
                if len(player.units) == 4:
                    actions.append(cityTile.build_cart())
                else:
                    actions.append(cityTile.build_worker())'''
            else:
                actions.append(cityTile.research())
########################################################################################################################
    ### UNITS
    # we iterate over all our units and do something with them
    for unit in player.units:
        if unit.is_worker() and unit.can_act():
            closestCityTile = getClosestCityTile(unit, player)
########################################################################################################################
            # NIGHT IS COMMING
            turnsToGetBack = unit.pos.distance_to(closestCityTile.pos) * 2
            turnsToNight = 30 - game_state.turn % 40
            if turnsToGetBack >= turnsToNight :
                actions.append(annotate.x(closestCityTile.pos.x,closestCityTile.pos.y))
                moveDirection = getBestMove(unit.pos, closestCityTile.pos, nextMoves, player, False)
                actions.append(unit.move(moveDirection))
                newCell = game_state.map.get_cell_by_pos(unit.pos.translate(moveDirection, 1))
                if newCell.citytile is None:
                    nextMoves.append(newCell.pos)
                actions.append(annotate.line(unit.pos.x,unit.pos.y,newCell.pos.x,newCell.pos.y))

########################################################################################################################
            # PREPARE FOR THE NIGHT
            elif unit.get_cargo_space_left() == 0:
                if not ImReadyForTheNight(player):
                    actions.append(annotate.x(closestCityTile.pos.x, closestCityTile.pos.y))
                    moveDirection = getBestMove(unit.pos, closestCityTile.pos, nextMoves, player, False)
                    actions.append(unit.move(moveDirection))
                    newCell = game_state.map.get_cell_by_pos(unit.pos.translate(moveDirection, 1))
                    if newCell.citytile is None:
                        nextMoves.append(newCell.pos)
                    actions.append(annotate.line(unit.pos.x,unit.pos.y,newCell.pos.x,newCell.pos.y))
########################################################################################################################
                # BUILD
                else:
                    actions.append(annotate.sidetext("READY"))
                    constructionSites = getConstructionSites(player)
                    if getCell(unit) in constructionSites:
                        actions.append(unit.build_city())
                    elif not building :
                        closestConstructionSite: Cell = None
                        csClosestDist = math.inf
                        for cs in constructionSites:
                            actions.append(annotate.circle(cs.pos.x,cs.pos.y))
                            dist = cs.pos.distance_to(unit.pos)
                            if dist < csClosestDist:
                                csClosestDist = dist
                                closestConstructionSite = cs
                        if closestConstructionSite is not None:
                            building = True
                            actions.append(annotate.x(closestConstructionSite.pos.x,closestConstructionSite.pos.y))
                            moveDirection = getBestMove(unit.pos, closestConstructionSite.pos, nextMoves, player, True)
                            actions.append(unit.move(moveDirection))
                            newCell = game_state.map.get_cell_by_pos(unit.pos.translate(moveDirection, 1))
                            if newCell.citytile is None:
                                nextMoves.append(newCell.pos)
                            actions.append(annotate.line(unit.pos.x,unit.pos.y,newCell.pos.x,newCell.pos.y))

########################################################################################################################
            # GATHER RESOURCES                                
            elif unit.get_cargo_space_left() > 0:
                closest_dist = math.inf
                closestResourceTile = None
                if unit.get_cargo_space_left() > 0:
                    # if the unit is a worker and we have space in cargo, lets find the nearest resource tile and try to mine it
                    for resource_tile in resourceTiles:
                        if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not player.researched_coal(): continue
                        if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not player.researched_uranium(): continue
                        dist = resource_tile.pos.distance_to(unit.pos)
                        if dist < closest_dist:
                            closest_dist = dist
                            closestResourceTile = resource_tile
                    if closestResourceTile is not None:
                        actions.append(annotate.x(closestResourceTile.pos.x,closestResourceTile.pos.y))
                        moveDirection = getBestMove(unit.pos, closestResourceTile.pos, nextMoves, player, False)
                        actions.append(unit.move(moveDirection))
                        newCell = game_state.map.get_cell_by_pos(unit.pos.translate(moveDirection, 1))
                        if newCell.citytile is None:
                            nextMoves.append(newCell.pos)
                        actions.append(annotate.line(unit.pos.x,unit.pos.y,newCell.pos.x,newCell.pos.y))

    return actions
