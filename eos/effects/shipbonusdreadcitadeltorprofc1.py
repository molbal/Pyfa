# shipBonusDreadCitadelTorpRofC1
#
# Used by:
# Ship: Phoenix
type = "passive"
def handler(fit, ship, context):
    fit.modules.filteredItemBoost(lambda mod: mod.item.requiresSkill("Citadel Torpedoes"),
                                  "speed", ship.getModifiedItemAttr("dreadnoughtShipBonusC1"), skill="Caldari Dreadnought")
