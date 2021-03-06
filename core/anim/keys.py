# import pymel.core as pm
import maya.cmds as cmds

# Should figure out a better way of doing this one:
from wh.core.util.decorators import *
from wh.core.util.action import *
from wh.util.lists import listDiff


class Keys(object):

    """For manipulating key values"""

    def __init__(self):
        super(Keys, self).__init__()

        if not pivotValue:
            pivotValue = cmds.keyframe(
                q=True, valueChange=True, lastSelected=True)[0]

        self.factor = factor
        self.individual = individual
        self.pivot = pivot
        self.pivotValue = pivotValue

    def scale(self):
        pass

    def contract(self):
        pass

    def exaggurate(self):
        pass

    def dampen(self):
        pass

    def copy(self):
        pass

    def flip(self):
        pass

    @staticmethod
    def iterateDecorator(fn):

        def wrapper(pivot=None, factor=1, pivotValue=None, individual=True):

            for curve in ActionCurves():

                if individual:
                    self.setPivotValueCurve(curve)

                for key in ActionKeys(curve):
                    return fn(self)

        return wrapper

    # @iterateDecorator
    def push(self):
        cmds.scaleKey(
            curve, index=key, valuePivot=self.pivotValue, valueScale=True / self.factor)

    # @iterateDecorator
    def pull(self):
        cmds.scaleKey(
            curve, index=key, valuePivot=self.pivotValue, valueScale=self.factor)

    def setPivotValueCurve(self, curve):

            timeArray = cmds.keyframe(
                curve, q=True, timeChange=True, selected=True)

            # per curve pivot value value
            if self.pivot == 'left':
                pivotTime = float(
                    cmds.findKeyframe(curve, which='previous', time=timeArray[0]))
                self.pivotValue = cmds.keyframe(
                    curve, q=True, valueChange=True, time=pivotTime)[0]

            if self.pivot == 'right':
                pivotTime = float(
                    cmds.findKeyframe(curve, which='next', time=timeArray[-1]))
                self.pivotValue = cmds.keyframe(
                    curve, q=True, valueChange=True, time=pivotTime)[0]


# KeyFrame().initialize()

class KeyFrames(object):

    """For manipulating KeyFrames"""

    def __init__(self, nodes=None, attrs=None, frameRange=None, step=1):
        super(KeyFrames, self).__init__()

        self.frameRange = frameRange
        self.nodes = ActionNodes(nodes=nodes)
        self.attrs = attrs
        self.step = step

    # Could use suspendAutoFrame decorator
    @undoChunkDecorator
    @restoreContextDecorator
    def breakdown(self, percent):

        for frame in ActionFrames(frameRange=self.frameRange, single=True, step=self.step):
            for node in self.nodes:
                for attr in ActionAttrs(node, attrs=self.attrs):

                    nextKey = int(
                        cmds.findKeyframe(node, t=(frame, frame), at=attr, which='next'))
                    prevKey = int(
                        cmds.findKeyframe(node, t=(frame, frame), at=attr, which='previous'))

                    # Set to current frame if previous or next key don't exist
                    if not nextKey:
                        nextKey = frame

                    if not prevKey:
                        prevKey = frame

                    # Get brakdown value
                    nodeAttr = node + '.' + attr
                    nextKeyValue = cmds.keyframe(
                        nodeAttr, t=(nextKey, nextKey), q=True, ev=True)[0]
                    prevKeyValue = cmds.keyframe(
                        nodeAttr, t=(prevKey, prevKey), q=True, ev=True)[0]
                    difference = nextKeyValue - prevKeyValue
                    newValue = difference * percent * .01 + prevKeyValue

                    # Faster
                    cmds.setKeyframe(
                        node, at=attr, t=(frame, frame), v=newValue)

                    # match previous and next tangents
                    ott = cmds.keyTangent(
                        node, at=attr, q=True, itt=True, t=(nextKey, nextKey))[0]
                    itt = cmds.keyTangent(
                        node, at=attr, q=True, ott=True, t=(prevKey, prevKey))[0]

                    if itt != 'step':
                        cmds.keyTangent(
                            node, at=attr, itt=itt, t=(frame, frame))

                    cmds.keyTangent(node, at=attr, ott=ott, t=(frame, frame))

    # Could use a suspendAutoFrame decorator
    # Don't set keyframe unless keyed attribut is keyed already. Maybe
    # setAttr, but make sure a key is set if it doesn't change the value?
    @undoChunkDecorator
    @restoreContextDecorator
    def initialize(self):
        for frame in ActionFrames(frameRange=self.frameRange, single=True, step=self.step):
            for node in self.nodes:
                for attr in ActionAttrs(node, attrs=self.attrs):

                    defaultValue = cmds.attributeQuery(
                        attr, node=node, ld=1)[0]
                    cmds.setKeyframe(
                        node, at=attr, t=(frame, frame), v=defaultValue)

    # Current implementation adjusts keys depending on tangent. Need alternative for this
    # bake should just be rekey on 1s
    @undoChunkDecorator
    @suspendRefreshDecorator
    @restoreContextDecorator
    def bake(self):

        for frame in ActionFrames(frameRange=self.frameRange, step=self.step):
            for node in self.nodes:
                for attr in ActionAttrs(node, attrs=self.attrs):
                    cmds.setKeyframe(node, at=attr, t=[frame, frame], i=True)

    @undoChunkDecorator
    @suspendRefreshDecorator
    @restoreContextDecorator
    def merge(self):

        for frame in ActionKeyFrames(self.nodes.nodes, frameRange=self.frameRange):
            cmds.setKeyframe(t=[frame, frame], i=True)

    def rekey(self):

        frames = ActionFrames(frameRange=self.frameRange, step=self.step)

        for frame in frames:
            for node in self.nodes:
                for attr in ActionAttrs(node, attrs=self.attrs):
                    cmds.setKeyframe(t=[frame, frame], i=True, at=attr)

        allFrames = range(frames.range['start'], frames.range['end'] + 1)
        keyedFrames = frames.frames
        removeFrames = listDiff(allFrames, keyedFrames)

        # Pull out into a new def remove(self):
        for frame in removeFrames:
            for node in self.nodes:
                for attr in ActionAttrs(node, attrs=self.attrs):
                    cmds.cutKey(time=(frame, frame), at=attr)

    def remove(self):
        pass
