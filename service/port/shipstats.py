from functools import reduce
from eos.saveddata.damagePattern import DamagePattern
from eos.utils.stats import RRTypes, DmgTypes
from gui.utils.numberFormatter import formatAmount

tankTypes = RRTypes.names()
damageTypes = DmgTypes.names()
damagePatterns = [DamagePattern.oneType(damageType) for damageType in damageTypes]
damageTypeResonanceNames = [damageType.capitalize() + "DamageResonance" for damageType in damageTypes]
resonanceNames = {tankTypes[0]: [tankTypes[0] + s for s in damageTypeResonanceNames],
                  tankTypes[1]: [tankTypes[1] + s for s in damageTypeResonanceNames],
                  tankTypes[2]: [s[0].lower() + s[1:] for s in damageTypeResonanceNames]}


def firepowerSection(fit):
    """ Returns the text of the firepower section"""
    totalDps = fit.getTotalDps().total
    weaponDps = fit.getWeaponDps().total
    droneDps = fit.getDroneDps().total
    totalVolley = fit.getTotalVolley().total
    firepower = [totalDps, weaponDps, droneDps, totalVolley]

    firepowerStr = [formatAmount(dps, 3, 0, 0) for dps in firepower]
    # showWeaponAndDroneDps = (weaponDps > 0) and (droneDps > 0)
    if sum(firepower) == 0:
        return ""

    return "DPS: {} (".format(firepowerStr[0]) + \
           ("Weapon: {}, Drone: {}, ".format(*firepowerStr[1:3])) + \
           ("Volley: {})\n".format(firepowerStr[3]))


def tankSection(fit):
    """ Returns the text of the tank section"""
    ehp = [fit.ehp[tank] for tank in tankTypes] if fit.ehp is not None else [0, 0, 0]
    ehp.append(sum(ehp))
    ehpStr = [formatAmount(ehpVal, 3, 0, 9) for ehpVal in ehp]
    resists = {tankType: [1 - fit.ship.getModifiedItemAttr(s) for s in resonanceNames[tankType]] for tankType in
               tankTypes}
    ehpAgainstDamageType = [sum(pattern.calculateEhp(fit).values()) for pattern in damagePatterns]
    ehpAgainstDamageTypeStr = [formatAmount(ehpVal, 3, 0, 9) for ehpVal in ehpAgainstDamageType]

    # not used for now.  maybe will be improved later
    # def formattedOutput():
    #     return \
    #         "        {:>7} {:>7} {:>7} {:>7} {:>7}\n".format("TOTAL", "EM", "THERM", "KIN", "EXP") + \
    #         "EHP     {:>7} {:>7} {:>7} {:>7} {:>7}\n".format(ehpStr[3], *ehpAgainstDamageTypeStr) + \
    #         "Shield  {:>7} {:>7.0%} {:>7.0%} {:>7.0%} {:>7.0%}\n".format(ehpStr[0], *resists["shield"]) + \
    #         "Armor   {:>7} {:>7.0%} {:>7.0%} {:>7.0%} {:>7.0%}\n".format(ehpStr[1], *resists["armor"]) + \
    #         "Hull    {:>7} {:>7.0%} {:>7.0%} {:>7.0%} {:>7.0%}\n".format(ehpStr[2], *resists["hull"])

    def generalOutput():
        rowNames = ["EHP"]
        rowNames.extend(RRTypes.names(postProcessor=lambda v: v.capitalize()))
        colNames = DmgTypes.names(short=True, postProcessor=lambda v: " " + v.capitalize())
        colNames[0] = colNames[0][1::]

        outputScheme = []
        for index, rowName in enumerate(rowNames):
            row = rowName + ": {:>} ("
            subsValue = " {:.0%}," if index > 0 else " {:>},"

            row += ''.join([(colName + ":" + subsValue) for colName in colNames])
            row = row[:-1:] + ")\n"

            outputScheme.append(row)

        return \
            outputScheme[0].format(ehpStr[3], *ehpAgainstDamageTypeStr) + \
            outputScheme[1].format(ehpStr[0], *resists["shield"]) + \
            outputScheme[2].format(ehpStr[1], *resists["armor"]) + \
            outputScheme[3].format(ehpStr[2], *resists["hull"])

        # return \
        #     "EHP: {:>} (Em: {:>}, Th: {:>}, Kin: {:>}, Exp: {:>})\n".format(ehpStr[3], *ehpAgainstDamageTypeStr) + \
        #     "Shield: {:>} (Em: {:.0%}, Th: {:.0%}, Kin: {:.0%}, Exp: {:.0%})\n".format(ehpStr[0], *resists["shield"]) + \
        #     "Armor: {:>} (Em: {:.0%}, Th: {:.0%}, Kin: {:.0%}, Exp: {:.0%})\n".format(ehpStr[1], *resists["armor"]) + \
        #     "Hull: {:>} (Em: {:.0%}, Th: {:.0%}, Kin: {:.0%}, Exp: {:.0%})\n".format(ehpStr[2], *resists["hull"])

    return generalOutput()


def _addFormattedColumn(value, name, header, linesList, repStr):
    if value:
        header += "{:>7} ".format(name)
        linesList = [line + "{:>7} ".format(rep) for line, rep in zip(linesList, repStr)]

    return header, linesList


def repsSection(fit):
    """ Returns the text of the repairs section"""
    selfRep = [fit.effectiveTank[tankType + "Repair"] for tankType in tankTypes]
    sustainRep = [fit.effectiveSustainableTank[tankType + "Repair"] for tankType in tankTypes]
    remoteRepObj = fit.getRemoteReps()
    remoteRep = [remoteRepObj.shield, remoteRepObj.armor, remoteRepObj.hull]
    shieldRegen = [fit.effectiveSustainableTank["passiveShield"], 0, 0]
    shieldRechargeModuleMultipliers = [module.item.attributes["shieldRechargeRateMultiplier"].value for module in
                                       fit.modules if
                                       module.item and "shieldRechargeRateMultiplier" in module.item.attributes]
    shieldRechargeMultiplierByModules = reduce(lambda x, y: x * y, shieldRechargeModuleMultipliers, 1)
    if shieldRechargeMultiplierByModules >= 0.9:  # If the total affect of modules on the shield recharge is negative or insignificant, we don't care about it
        shieldRegen[0] = 0
    totalRep = list(zip(selfRep, remoteRep, shieldRegen))
    totalRep = list(map(sum, totalRep))

    selfRep.append(sum(selfRep))
    sustainRep.append(sum(sustainRep))
    remoteRep.append(sum(remoteRep))
    shieldRegen.append(sum(shieldRegen))
    totalRep.append(sum(totalRep))

    totalSelfRep = selfRep[-1]
    totalRemoteRep = remoteRep[-1]
    totalShieldRegen = shieldRegen[-1]

    text = ""

    if sum(totalRep) > 0:  # Most commonly, there are no reps at all; then we skip this section
        singleTypeRep = None
        singleTypeRepName = None
        if totalRemoteRep == 0 and totalShieldRegen == 0:  # Only self rep
            singleTypeRep = selfRep[:-1]
            singleTypeRepName = "Self"
        if totalSelfRep == 0 and totalShieldRegen == 0:  # Only remote rep
            singleTypeRep = remoteRep[:-1]
            singleTypeRepName = "Remote"
        if totalSelfRep == 0 and totalRemoteRep == 0:  # Only shield regen
            singleTypeRep = shieldRegen[:-1]
            singleTypeRepName = "Regen"
        if singleTypeRep and sum(
                x > 0 for x in singleTypeRep) == 1:  # Only one type of reps and only one tank type is repaired
            index = next(i for i, v in enumerate(singleTypeRep) if v > 0)
            if singleTypeRepName == "Regen":
                text += "Shield regeneration: {} EHP/s".format(formatAmount(singleTypeRep[index], 3, 0, 9))
            else:
                text += "{} {} repair: {} EHP/s".format(singleTypeRepName, tankTypes[index],
                                                        formatAmount(singleTypeRep[index], 3, 0, 9))
            if (singleTypeRepName == "Self") and (sustainRep[index] != singleTypeRep[index]):
                text += " (Sustained: {} EHP/s)".format(formatAmount(sustainRep[index], 3, 0, 9))
            text += "\n"
        else:  # Otherwise show a table
            selfRepStr = [formatAmount(rep, 3, 0, 9) for rep in selfRep]
            sustainRepStr = [formatAmount(rep, 3, 0, 9) for rep in sustainRep]
            remoteRepStr = [formatAmount(rep, 3, 0, 9) for rep in remoteRep]
            shieldRegenStr = [formatAmount(rep, 3, 0, 9) if rep != 0 else "" for rep in shieldRegen]
            totalRepStr = [formatAmount(rep, 3, 0, 9) for rep in totalRep]

            lines = RRTypes.names(postProcessor=lambda v: v.capitalize())
            lines.append("Total")
            lines = ["{:<8}".format(line) for line in lines]

            showSelfRepColumn = totalSelfRep > 0
            showSustainRepColumn = sustainRep != selfRep
            showRemoteRepColumn = totalRemoteRep > 0
            showShieldRegenColumn = totalShieldRegen > 0

            header = "REPS    "
            header, lines = _addFormattedColumn(
                (showSelfRepColumn + showSustainRepColumn + showRemoteRepColumn + showShieldRegenColumn > 1),
                "TOTAL", header, lines, totalRepStr)
            header, lines = _addFormattedColumn(showSelfRepColumn, "SELF", header, lines, selfRepStr)
            header, lines = _addFormattedColumn(showSustainRepColumn, "SUST", header, lines, sustainRepStr)
            header, lines = _addFormattedColumn(showRemoteRepColumn, "REMOTE", header, lines, remoteRepStr)
            header, lines = _addFormattedColumn(showShieldRegenColumn, "REGEN", header, lines, shieldRegenStr)

            text += header + "\n"
            repsByTank = zip(totalRep, selfRep, sustainRep, remoteRep, shieldRegen)
            for line in lines:
                reps = next(repsByTank)
                if sum(reps) > 0:
                    text += line + "\n"
    return text


def miscSection(fit):
    text = ""
    text += "Speed: {} m/s\n".format(formatAmount(fit.maxSpeed, 3, 0, 0))
    text += "Signature: {} m\n".format(formatAmount(fit.ship.getModifiedItemAttr("signatureRadius"), 3, 0, 9))

    text += "Capacitor: {} GJ".format(formatAmount(fit.ship.getModifiedItemAttr("capacitorCapacity"), 3, 0, 9))
    capState = fit.capState
    if fit.capStable:
        text += " (Stable at {0:.0f}%)".format(capState)
    else:
        text += " (Lasts {})".format("%ds" % capState if capState <= 60 else "%dm%ds" % divmod(capState, 60))
    text += "\n"

    text += "Targeting range: {} km\n".format(formatAmount(fit.maxTargetRange / 1000, 3, 0, 0))
    text += "Scan resolution: {0:.0f} mm\n".format(fit.ship.getModifiedItemAttr("scanResolution"))
    text += "Sensor strength: {}\n".format(formatAmount(fit.scanStrength, 3, 0, 0))

    return text


def exportAsJson(fit, callback):
    import json
    ehp = [fit.ehp[tank] for tank in tankTypes] if fit.ehp is not None else [0, 0, 0]
    ehp.append(sum(ehp))
    resists = {tankType: [1 - fit.ship.getModifiedItemAttr(s) for s in resonanceNames[tankType]] for tankType in
               tankTypes}

    selfRep = [fit.effectiveTank[tankType + "Repair"] for tankType in tankTypes]
    sustainRep = [fit.effectiveSustainableTank[tankType + "Repair"] for tankType in tankTypes]
    remoteRepObj = fit.getRemoteReps()
    remoteRep = [remoteRepObj.shield, remoteRepObj.armor, remoteRepObj.hull]
    shieldRegen = [fit.effectiveSustainableTank["passiveShield"], 0, 0]

    cpuUsed = fit.cpuUsed
    pgUsed = fit.pgUsed
    calibrationUsed = fit.calibrationUsed
    droneBandwidthUsed = fit.droneBandwidthUsed
    droneBayUsed = fit.droneBayUsed
    activeDrones = fit.activeDrones
    warpSpeed = fit.warpSpeed
    from eos.utils.spoolSupport import SpoolOptions
    data = {
        "offense": {
            "totalDps": round(fit.getTotalDps(spoolOptions=SpoolOptions(0, 1, True)).total, 2),
            "weaponDps": round(fit.getWeaponDps(spoolOptions=SpoolOptions(0, 1, True)).total, 2),
            "droneDps": round(fit.getDroneDps().total, 2),
            "totalVolley": round(fit.getTotalVolley().total, 2)
        },
        "defense": {
            "ehp": {
                "total": ehp[3],
                "shield": ehp[0],
                "armor": ehp[1],
                "hull": ehp[2]
            },
            "resists": {
                "shield": {
                    "em": round(resists["shield"][0], 4),
                    "therm": round(resists["shield"][1], 4),
                    "kin": round(resists["shield"][2], 4),
                    "exp": round(resists["shield"][3], 4)
                },
                "armor": {
                    "em": round(resists["armor"][0], 4),
                    "therm": round(resists["armor"][1], 4),
                    "kin": round(resists["armor"][2], 4),
                    "exp": round(resists["armor"][3], 4)
                },
                "hull": {
                    "em": round(resists["hull"][0], 4),
                    "therm": round(resists["hull"][1], 4),
                    "kin": round(resists["hull"][2], 4),
                    "exp": round(resists["hull"][3], 4)
                }
            },
            "reps": {
                "burst": {
                    "shieldRegen": round(shieldRegen[0], 2),
                    "shieldBoost": round(selfRep[0], 2),
                    "armor": round(selfRep[1], 2),
                    "hull": round(selfRep[2], 2),
                    "total": round(shieldRegen[0] + selfRep[0] + selfRep[1] + selfRep[2], 2)
                },
                "sustained": {
                    "shieldRegen": round(shieldRegen[0], 2),
                    "shieldBoost": round(sustainRep[0], 2),
                    "armor": round(sustainRep[1], 2),
                    "hull": round(sustainRep[2], 2),
                    "total": round(shieldRegen[0] + sustainRep[0] + sustainRep[1] + sustainRep[2], 2)
                }
            }
        },
        "misc": {
            "ship": {
                "id":   fit.ship.item.ID,
                "name": fit.ship.item.name,
                "cpuMax": round(fit.ship.getModifiedItemAttr("cpuOutput"), 2),
                "powerMax": round(fit.ship.getModifiedItemAttr("powerOutput"), 2),
                "cpuUsed": cpuUsed,
                "pgUsed": pgUsed,
                "calibrationUsed": calibrationUsed,
                "warpSpeed": warpSpeed
                # "cpuUsage": round(fit.cpuUsed(), 2)
                # "all": fit.ship.itemModifiedAttributes.
            },
            "drones": {
                "activeDrones": activeDrones,
                "droneBayTotal": fit.ship.getModifiedItemAttr("droneCapacity"),
                "droneBandwidthUsed": droneBandwidthUsed,
                "droneBayUsed": droneBayUsed,
            },
            "maxSpeed": round(fit.maxSpeed, 2),
            "signature": round(fit.ship.getModifiedItemAttr("signatureRadius"), 2),
            "capacitor": {
                "capacity": round(fit.ship.getModifiedItemAttr("capacitorCapacity"), 2),
                "stable": fit.capStable,
                "stableAt": round(fit.capState, 2) if fit.capStable else None,
                "lastsSeconds": round(fit.capState, 2) if not fit.capStable else None
            },
            "targeting": {
                "range": fit.maxTargetRange,
                "resolution": fit.ship.getModifiedItemAttr("scanResolution"),
                "strength": fit.scanStrength
            }
        }
    }
    from eos.const import SpoolType
    return json.dumps(data)


def exportFitStats(fit, callback):
    """
    Returns the text of the stats export of the given fit
    """
    sections = filter(None, (firepowerSection(fit),  # Prune empty sections
                             tankSection(fit),
                             repsSection(fit),
                             miscSection(fit)))

    text = "{} ({})\n".format(fit.name, fit.ship.name) + "\n"
    text += "\n".join(sections)

    if callback:
        callback(text)
    else:
        return text
